import pandas as pd
import geopandas as gpd
from datetime import date
import pathlib


# Path to the data folder
data_folder = pathlib.Path().absolute() / 'data'

def getCovidCases():    
    # Path to the data file
    data_file = data_folder / f'covid19_{date.today()}.csv'

    # Get data from API
    if  data_file.exists():
        # Read csv from existing file
        covid_cases = pd.read_csv(data_file, encoding='latin-1')
    else:
        # Read csv from url
        covid_cases = pd.read_csv('https://indicadores.integrasus.saude.ce.gov.br/api/casos-coronavirus/export-csv', encoding='latin-1')
        covid_cases.to_csv(data_file, index=False, encoding='latin-1')
    
    return covid_cases

def getGeoData():
    # Get neighborhoods geospatial data from official database
    geojson_file = data_folder / 'neighborhood_geospatial_information.geojson'

    if  geojson_file.exists():
        # Read csv from existing file
        geo_neighborhoods = gpd.read_file(geojson_file)
    else:
        # Read json from url
        geo_neighborhoods = gpd.read_file('https://dados.fortaleza.ce.gov.br/dataset/8d20208f-25d6-4ca3-b0bc-1b9b371bd062/resource/781b13ec-b479-4b97-a742-d3b7144672ee/download/limitebairro.json')
        geo_neighborhoods.to_file(geojson_file, driver='GeoJSON')
    
    return geo_neighborhoods