# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
from datetime import date
from datetime import datetime
from unicodedata import normalize
from Levenshtein import distance
import geopandas as gpd
from shapely.geometry import Polygon
import folium
from folium.features import DivIcon
import pathlib

# Remove .loc warning s
pd.options.mode.chained_assignment = None

# Path to the data folder
data_folder = pathlib.Path().absolute() / 'data'

# Get data from API
data_file = data_folder / f'covid19_{date.today()}.csv'

if  data_file.exists():
    # Read csv from existing file
    covid_cases = pd.read_csv(data_file, encoding='latin-1')
else:
    # Read csv from url
    covid_cases = pd.read_csv('https://indicadores.integrasus.saude.ce.gov.br/api/casos-coronavirus/export-csv', encoding='latin-1')
    covid_cases.to_csv(data_file, index=False, encoding='latin-1')

# Get neighborhoods geospatial data from official database
geojson_file = data_folder / 'neighborhood_geospatial_information.geojson'

if  geojson_file.exists():
    # Read csv from existing file
    geo_neighborhoods = gpd.read_file(geojson_file)
else:
    # Read json from url
    geo_neighborhoods = gpd.read_file('https://dados.fortaleza.ce.gov.br/dataset/8d20208f-25d6-4ca3-b0bc-1b9b371bd062/resource/781b13ec-b479-4b97-a742-d3b7144672ee/download/limitebairro.json')
    geo_neighborhoods.to_file(geojson_file, driver='GeoJSON')

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

def clean_text(raw_text):
    cleaned_text = remove_special_characters(raw_text)
    cleaned_text = cleaned_text.strip()
    cleaned_text = remove_accents(cleaned_text)
    cleaned_text = cleaned_text.upper()

    return cleaned_text

def min_edit_distance(word, list_of_words):    
    if word == 'NAO INFORMADO':
        return 'NAO INFORMADO'

    word_dict = {}
    
    for aux in list_of_words:
        word_dict[aux] = distance(aux, word)

    return min(word_dict.keys(), key=(lambda k: word_dict[k]))

# Rename columns
covid_cases.columns = ['bairroPaciente', 'classificacaoEstadoSivep', 'codigoMunicipioPaciente','codigoPaciente', 'comorbidadeAsmaSivep', 'comorbidadeCardiovascularSivep', 'comorbidadeDiabetesSivep', 
                       'comorbidadeHematologiaSivep', 'comorbidadeImunodeficienciaSivep', 'comorbidadeNeurologiaSivep', 'comorbidadeObesidadeSivep', 'comorbidadePneumopatiaSivep', 'comorbidadePuerperaSivep', 
                       'comorbidadeRenalSivep', 'comorbidadeSindromedownSivep', 'dataColetaExame', 'dataEntradaUtisSivep', 'dataEvolucaoCasoSivep', 'dataInicioSintomas', 'dataInternacaoSivep', 'dataNotificacao', 
                       'dataObito', 'dataResultadoExame', 'dataSaidaUtisSivep', 'dataSolicitacaoExame',  'estadoPaciente', 'evolucaoCasoSivep', 'idadePaciente', 'idSivep', 'municipioPaciente', 'obitoConfirmado', 
                       'paisPaciente', 'resultadoFinalExame', 'sexoPaciente']

# Convert string to datetime
covid_cases['dataNotificacao'] = pd.to_datetime(covid_cases['dataNotificacao'], errors='coerce')
covid_cases['dataInicioSintomas'] = pd.to_datetime(covid_cases['dataInicioSintomas'], errors='coerce')
covid_cases['dataColetaExame'] = pd.to_datetime(covid_cases['dataColetaExame'], errors='coerce')
covid_cases['dataResultadoExame'] = pd.to_datetime(covid_cases['dataResultadoExame'], errors='coerce')

# Selecting rows of the city Fortaleza
covid_cases = covid_cases[(covid_cases['municipioPaciente'] == 'FORTALEZA')]

# Get only positive results
covid_cases = covid_cases[(covid_cases['resultadoFinalExame'] == 'Positivo')]

# Remove duplicate codes keeping the first appearance
covid_cases = covid_cases.sort_values('bairroPaciente').drop_duplicates(subset='codigoPaciente', keep='first')

# Remove NaNs from neighborhoods
covid_cases['bairroPaciente'].fillna('NAO INFORMADO', inplace=True)

# Clean neighborhoods names
covid_cases['bairroPaciente'] = covid_cases['bairroPaciente'].map(clean_text)

# Get official neighborhoods names
official_neighborhoods_names = geo_neighborhoods['NOME'].tolist()

# For each row it will compare the name of the row neighborhood to the official list and pick the closest name based on the minimum edit distance
covid_cases['bairroPaciente'] = covid_cases['bairroPaciente'].apply(min_edit_distance, list_of_words = official_neighborhoods_names)

positive_cases_by_neighborhood = covid_cases.groupby('bairroPaciente').count()['codigoPaciente']

# Get positive cases of rows with neighborhood information
positive_cases_by_neighborhood_only_known_names = covid_cases[covid_cases['bairroPaciente'] != 'NAO INFORMADO'].groupby('bairroPaciente').count()['codigoPaciente']

# Get positive cases of rows with no neighborhood information
positive_cases_no_information_neighborhoods = covid_cases[covid_cases['bairroPaciente'] == 'NAO INFORMADO'].count()['codigoPaciente']

positive_cases_total = covid_cases['codigoPaciente'].count()

deaths_by_neighborhood = covid_cases[covid_cases['obitoConfirmado'] == True].groupby('bairroPaciente').count()['codigoPaciente']

# Get deaths of rows with no neighborhood information
deaths_no_information_neighborhoods = covid_cases[(covid_cases['obitoConfirmado'] == True) & (covid_cases['bairroPaciente'] == 'NAO INFORMADO')].count()['codigoPaciente']

deaths_total = covid_cases[covid_cases['obitoConfirmado'] == True].count()['codigoPaciente']

# Merge geo_neighborhoods and positive_cases_by_neighborhood
geo_neighborhoods = pd.merge(left=geo_neighborhoods, right=positive_cases_by_neighborhood, left_on='NOME', right_on='bairroPaciente', how='left')
geo_neighborhoods.rename(columns={'codigoPaciente': 'CASOS_POSITIVOS'}, inplace=True)
geo_neighborhoods['CASOS_POSITIVOS'].fillna(0, inplace=True)

# Merge geo_neighborhoods and deaths_by_neighborhood
geo_neighborhoods = pd.merge(left=geo_neighborhoods, right=deaths_by_neighborhood, left_on='NOME', right_on='bairroPaciente', how='left')
geo_neighborhoods.rename(columns={'codigoPaciente': 'OBITOS_CONFIRMADOS'}, inplace=True)
geo_neighborhoods['OBITOS_CONFIRMADOS'].fillna(0, inplace=True)

# Convert to WGS84
geo_neighborhoods = geo_neighborhoods.to_crs(epsg=4326).to_json()

# Create folium map
map = folium.Map(location=[-3.7981414, -38.5218430], zoom_start=12)

choropleth = folium.Choropleth(
            geo_data=geo_neighborhoods,
            name='choropleth',
            data=positive_cases_by_neighborhood_only_known_names,
            columns=['codigoPaciente'],
            key_on='feature.properties.NOME',
            fill_color='YlOrRd',
            fill_opacity=0.6,
            line_opacity=0.2,
            highlight=True,
            legend_name='Casos confirmados de Covid-19 em Fortaleza-CE'
).add_to(map)

choropleth.geojson.add_child(folium.features.GeoJsonTooltip(fields=['NOME', 'CASOS_POSITIVOS', 'OBITOS_CONFIRMADOS'], aliases=['Bairro:', 'Casos confirmados:', 'Óbitos confirmados:']))

folium.map.Marker(
    [-3.68, -38.5399999],
    icon=DivIcon(
        icon_size=(150,100),
        icon_anchor=(0,0),
        html=f'<div style="font-size:10px;">Bairro: NÃO INFORMADO<br> Casos Confirmados: {positive_cases_no_information_neighborhoods}<br>Óbitos Confirmados: {deaths_no_information_neighborhoods}</div>',
        )
    ).add_to(map)

folium.map.Marker(
    [-3.7, -38.3999999],
    icon=DivIcon(
        icon_size=(400,300),
        icon_anchor=(0,0),
        html=f'<div style="font-size:20px;font-weight:bold">Total de Casos Confirmados: {positive_cases_total}<br>Total de Óbitos Confirmados: {deaths_total}</div>',
        )
    ).add_to(map)

map

map.save('Covid-19_confirmed_cases_fortaleza.html')

app = dash.Dash(__name__)

server = app.server

app.layout = html.Div([
        html.Div([
            html.H2(f'Casos confirmados de Covid-19 em Fortaleza-CE - Atualizado: {datetime.now().strftime("%d/%m/%Y")}'),
            html.Iframe(id='map', srcDoc=open('Covid-19_confirmed_cases_fortaleza.html', 'r').read(), width='800', height='800', className='iframe')
        ], className='two.columns')
    ], className='row')

if __name__ == '__main__':
    app.run_server(debug=True)