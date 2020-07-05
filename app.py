from datetime import datetime, date, timedelta
import pytz
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
from rq import Queue
from worker import conn

import data
import data_cleaning
import map

queue = Queue(connection=conn)

def job():
    # Get required data
    covid_cases = data.getCovidCases()
    geo_neighborhoods = data.getGeoData()
    
    # Clean data
    clean_data = data_cleaning.clean_data(covid_cases, geo_neighborhoods)
    
    # Create map
    map.create_map(clean_data)

    map_html = open('Covid-19_confirmed_cases_fortaleza.html', 'r').read()

    print(map_html.split('Total de Casos Confirmados: ')[1])

    return map_html

map_html_job = queue.enqueue(job)

# Create app
app = dash.Dash(__name__)

server = app.server

def serve_layout():
    if map_html_job.result is None:
        map_html = open('Covid-19_confirmed_cases_fortaleza.html', 'r').read()
    else:
        map_html = map_html_job.result

    return html.Div([
        html.Div([
            html.H2(f'Casos confirmados de Covid-19 em Fortaleza-CE - Atualizado: {(pytz.utc.localize(datetime.utcnow()) - timedelta(hours=3)).strftime("%d/%m/%Y, %H:%M:%S")}'),
            html.A('Github onde está hospedado o código.', href='https://github.com/guifa/covid19-ce-real-time-dashboard'),
            html.Div([
                html.Div(map_html.split('Total de Casos Confirmados: ')[1], hidden=True),
                html.Iframe(id='map', srcDoc=map_html, width='800', height='800', className='iframe')
            ])
        ], className='two.columns')
    ], className='row')

app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(dev_tools_hot_reload=False)