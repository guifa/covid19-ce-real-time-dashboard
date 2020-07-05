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

map_html_ = job()

# Create app
app = dash.Dash(__name__)

server = app.server

app.layout = html.Div([
        html.Div([
            html.Div(id='title-container'),
            html.A('Github onde está hospedado o código.', href='https://github.com/guifa/covid19-ce-real-time-dashboard'),
            html.Div(id='map-container'),            
            dcc.Interval(
            id='interval-component',
            interval=30*1000, # in milliseconds
            n_intervals=0
        )
        ], className='two.columns')
    ], className='row')

@app.callback(Output('map-container', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_map(n):
    if map_html_job.result is None:
        map_html = open('Covid-19_confirmed_cases_fortaleza.html', 'r').read()

        return [
            html.Div(map_html.split('Total de Casos Confirmados: ')[1], hidden=True),
            html.Iframe(id='map', srcDoc=map_html, width='800', height='800', className='iframe')
        ]
    else:
        map_html = map_html_job.result
        return [
            html.Div(map_html.split('Total de Casos Confirmados: ')[1], hidden=True),
            html.Iframe(id='map', srcDoc=map_html, width='800', height='800', className='iframe')
        ]
            
    

@app.callback(Output('title-container', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_title(n):
    return html.H2(f'Casos confirmados de Covid-19 em Fortaleza-CE - Atualizado: {(pytz.utc.localize(datetime.utcnow()) - timedelta(hours=3)).strftime("%d/%m/%Y, %H:%M:%S")}')

if __name__ == '__main__':
    app.run_server(dev_tools_hot_reload=False)