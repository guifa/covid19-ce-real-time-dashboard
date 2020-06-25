# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
from datetime import date
from unicodedata import normalize
from Levenshtein import distance
import geopandas as gpd
from shapely.geometry import Polygon
import folium
from folium.features import DivIcon

response = requests.get(f"https://indicadores.integrasus.saude.ce.gov.br/api/casos-coronavirus?dataInicio=2020-01-01&dataFim={date.today()}")
json = response.json()

if response.status_code == 200:
    cases_covid = pd.DataFrame(json)

# Oficial data with names of neighborhoods
bairros = pd.read_csv('http://dados.fortaleza.ce.gov.br/dataset/8d20208f-25d6-4ca3-b0bc-1b9b371bd062/resource/3ba368fe-d585-4681-a987-6e288bdfffe0/download/limitebairro.csv')

def remove_accents(txt):
    return normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')

def remove_special_characters(text):
    a_string = text
    alphanumeric = ""

    for character in a_string:
        if character == " ":
            alphanumeric += character
        else:
            if character.isalnum():
                alphanumeric += character

    return alphanumeric

def clean_neighborhood_names(text):
    no_special_characters = remove_special_characters(text)
    trim_spaces = no_special_characters.strip()
    cleaned_neighborhood_names = remove_accents(trim_spaces)

    return cleaned_neighborhood_names

def replace_for_official_names(neighborhood_name, official_neighborhood_names):
    for name in official_neighborhood_names:
        if distance(neighborhood_name, name) < 5:
            return name
    return 'NAO INFORMADO'

cases_covid_fortaleza = cases_covid[cases_covid['municipioPaciente'] == 'FORTALEZA']

cases_covid_fortaleza_no_nan = cases_covid_fortaleza

cases_covid_fortaleza_no_nan['bairroPaciente'].fillna('NAO INFORMADO', inplace=True)

cases_covid_fortaleza_no_nan.loc[:, 'bairroPaciente'] = cases_covid_fortaleza_no_nan['bairroPaciente'].map(clean_neighborhood_names)

cases_covid_fortaleza_cleaned = cases_covid_fortaleza_no_nan

neighborhood_list = bairros['NOME'].tolist()

cases_covid_fortaleza_cleaned.loc[:, 'bairroPaciente'] = cases_covid_fortaleza_cleaned['bairroPaciente'].apply(replace_for_official_names, official_neighborhood_names = neighborhood_list)

cases_covid_fortaleza_cleaned_grouped_neighborhood = cases_covid_fortaleza_cleaned.groupby('bairroPaciente')

cases_covid_fortaleza_cleaned_positive = cases_covid_fortaleza_cleaned[cases_covid_fortaleza_cleaned['resultadoFinalExame'] == 'Positivo']

cases_covid_fortaleza_cleaned_positive_deaths = cases_covid_fortaleza_cleaned_positive[cases_covid_fortaleza_cleaned_positive['obitoConfirmado'] == True]

geo_bairros = gpd.read_file('https://dados.fortaleza.ce.gov.br/dataset/8d20208f-25d6-4ca3-b0bc-1b9b371bd062/resource/781b13ec-b479-4b97-a742-d3b7144672ee/download/limitebairro.json')

map_nao_informado = Polygon([(-38.5348892, -3.6799472),
                             (-38.5348892, -3.6799472),
                             (-38.5359192, -3.6967352),
                             (-38.5084534, -3.697763),
                             (-38.5060501, -3.6830307),
                             (-38.5348892, -3.6799472)])

df_bairros_nao_informados = pd.DataFrame({'id': ['Limite Bairro.nao-informado'],
                                          'GID': [9999],
                                          'NOME': ['NAO INFORMADO'],
                                          'geometry': map_nao_informado})

gdf_bairros_nao_informados = gpd.GeoDataFrame(df_bairros_nao_informados)

todos_bairros = pd.concat([geo_bairros, gdf_bairros_nao_informados])

casos_positivos = cases_covid_fortaleza_cleaned_positive.groupby('bairroPaciente').count()['codigoPaciente']

casos_positivos_total = cases_covid_fortaleza_cleaned_positive['codigoPaciente'].count()

obitos_por_covid = cases_covid_fortaleza_cleaned_positive_deaths.groupby('bairroPaciente').count()['codigoPaciente']

obitos_total = cases_covid_fortaleza_cleaned_positive_deaths['codigoPaciente'].count()

geo_todos_bairros_casos_positivos = pd.merge(left=todos_bairros, right=casos_positivos, left_on='NOME', right_on='bairroPaciente', how='left')
geo_todos_bairros_casos_positivos.rename(columns={'codigoPaciente': 'CASOS_POSITIVOS'}, inplace=True)
geo_todos_bairros_casos_positivos['CASOS_POSITIVOS'].fillna(0, inplace=True)
geo_todos_bairros_casos_positivos

geo_todos_bairros_casos_positivos_mortes = pd.merge(left=geo_todos_bairros_casos_positivos, right=obitos_por_covid, left_on='NOME', right_on='bairroPaciente', how='left')
geo_todos_bairros_casos_positivos_mortes.rename(columns={'codigoPaciente': 'OBITOS_CONFIRMADOS'}, inplace=True)
geo_todos_bairros_casos_positivos_mortes['OBITOS_CONFIRMADOS'].fillna(0, inplace=True)
geo_todos_bairros_casos_positivos_mortes

geo_todos_bairros_casos_positivos_mortes_crs_4326 = geo_todos_bairros_casos_positivos_mortes.to_crs(epsg=4326)

geo_todos_bairros_casos_positivos_mortes_crs_4326_json = geo_todos_bairros_casos_positivos_mortes_crs_4326.to_json()


m = folium.Map(location=[-3.7981414, -38.5218430], zoom_start=12)

choropleth = folium.Choropleth(
            geo_data=geo_todos_bairros_casos_positivos_mortes_crs_4326_json,
            name='choropleth',
            data=casos_positivos,
            columns=['codigoPaciente'],
            key_on='feature.properties.NOME',
            fill_color='YlOrRd',
            fill_opacity=0.6,
            line_opacity=0.2,
            highlight=True,
            legend_name='Casos confirmados de Covid-19 em Fortaleza-CE'
).add_to(m)

choropleth.geojson.add_child(folium.features.GeoJsonTooltip(fields=['NOME', 'CASOS_POSITIVOS', 'OBITOS_CONFIRMADOS'], aliases=['Bairro:', 'Casos confirmados:', 'Óbitos confirmados:']))

folium.map.Marker(
    [-3.6754932, -38.4483719],
    icon=DivIcon(
        icon_size=(150,150),
        icon_anchor=(0,0),
        html=f'<div style="font-size:10;font-weight:bold">Total de Casos Confirmados: {casos_positivos_total}<br>Total de Óbitos Confirmados: {obitos_total}</div>',
        )
    ).add_to(m)

m.save('Covid-19_confirmed_cases_fortaleza.html')

app = dash.Dash(__name__)

server = app.server

app.layout = html.Div([
        html.Div([
            html.H1('Casos confirmados de Covid-19 em Fortaleza-CE'),
            html.Iframe(id='map', srcDoc=open('Covid-19_confirmed_cases_fortaleza.html', 'r').read(), width='800', height='800', className='iframe')
        ], className='two.columns')
    ], className='row')

if __name__ == '__main__':
    app.run_server(debug=True)