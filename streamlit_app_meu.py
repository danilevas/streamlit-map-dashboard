import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import geojson

APP_TITLE = 'FOCO'
APP_SUB_TITLE = 'Ferramenta de Otimização do Custo de Oportunidade'
with open('data_meu/Limite_de_Bairros.geojson', 'r', encoding='utf-8') as file:
    data_geojson = geojson.load(file)

def ajeita_geojson():
    for feature in data_geojson['features']:
        while feature['properties']['nome'][-1] == " ":
            feature['properties']['nome'] = feature['properties']['nome'][:-1]

def display_bairro_filter(df, bairro_name):
    bairro_list = [''] + list(df['Bairro'].unique())
    bairro_list.sort()
    bairro_index = bairro_list.index(bairro_name) if bairro_name and bairro_name in bairro_list else 0
    return st.sidebar.selectbox('Bairro', bairro_list, bairro_index)

def display_map(df):
    map = folium.Map(location=[-22.91798994895881, -43.42464638599411], zoom_start=10, scrollWheelZoom=False, tiles='CartoDB positron')
    
    choropleth = folium.Choropleth(
        geo_data=data_geojson,
        data=df,
        columns=('Bairro', 'Fator Mapa'),
        key_on='feature.properties.nome',
        line_opacity=0.8,
        highlight=True
    )
    choropleth.geojson.add_to(map)

    df_indexed = df.set_index('Bairro')
    for feature in choropleth.geojson.data['features']:
        bairro_name = feature['properties']['nome']
        feature['properties']['ranking'] = 'Ranking: ' + '{:,}'.format(df_indexed.loc[bairro_name, 'Ranking']) if bairro_name in list(df_indexed.index) else ''
        feature['properties']['cdo'] = 'Custo de Oportunidade: ' + str(round(df_indexed.loc[bairro_name, 'CdO'], 2)) if bairro_name in list(df_indexed.index) else ''

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['nome', 'ranking', 'cdo'], labels=False)
    )
    
    st_map = st_folium(map, width=700, height=450)

    bairro_name = ''
    if st_map['last_active_drawing']:
        bairro_name = st_map['last_active_drawing']['properties']['nome']
    
    return bairro_name

def display_facts(df, bairro_name, field, title, string_format='{:,}', is_median=False):
    if bairro_name:
        df = df[df['Bairro'] == bairro_name]
    df.drop_duplicates(inplace=True)
    if is_median:
        total = df[field].sum() / len(df[field]) if len(df) else 0
    else:
        total = df[field].sum()
    st.metric(title, string_format.format(round(total, 2)))

def main():
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)
    st.caption(APP_SUB_TITLE)

    # Load Data
    df_bairros = pd.read_csv('data_meu/bairros_mapa.csv', encoding="utf-8")

    # Ajeita o geojson para que os nomes dos bairros não tenham espaços no final 
    ajeita_geojson()

    # Display Filters and Map
    bairro_name = display_map(df_bairros)
    bairro_name = display_bairro_filter(df_bairros, bairro_name)

    # Display Metrics
    st.subheader(f'Informações sobre {bairro_name}')

    col1, col2 = st.columns(2)
    with col1:
        display_facts(df_bairros, bairro_name, 'Ranking', f'Ranking', string_format='{:,}')
    with col2:
        display_facts(df_bairros, bairro_name, 'CdO', 'Custo de Oportunidade', is_median=True)

if __name__ == "__main__":
    main()