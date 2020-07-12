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
import db_connection

# Create redis queue
queue = Queue(connection=conn)

# Create database cursor to execute sql commands
cursor = db_connection.conn.cursor()

def job():
    cursor = db_connection.conn.cursor()
    
    # Get required data
    covid_cases = data.getCovidCases()
    geo_neighborhoods = data.getGeoData()
    
    # Clean data
    clean_data = data_cleaning.clean_data(covid_cases, geo_neighborhoods)
    
    # Create map
    map.create_map(clean_data)

    map_html = open('Covid-19_confirmed_cases_fortaleza.html', 'r').read()

    cursor.execute('UPDATE COVID19 SET MAP_HTML = %s WHERE ID = 1', (map_html,))

    db_connection.conn.commit()

# Enqueue job that will update map
queue.enqueue(job)

# Create app
app = dash.Dash(__name__, external_stylesheets=['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'])

app.title='Casos Covid-19 em Fortaleza-CE'

server = app.server

def serve_layout():
    cursor.execute("SELECT * FROM COVID19")
    row = cursor.fetchone()

    map_html = row[1]

    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.H1('Casos confirmados de Covid-19 em Fortaleza-CE'),
                    html.P(f'Atualizado: {(pytz.utc.localize(datetime.utcnow()) - timedelta(hours=3)).strftime("%d/%m/%Y, %H:%M:%S")}'),
                    html.A('Github', href='https://github.com/guifa/covid19-ce-real-time-dashboard', className='fa fa-github fa-4')                    
                ], className='inner')
            ], id='banner'),
            html.Div([
                html.Iframe(id='map', srcDoc=map_html, width='100%', height='800', className='iframe')
            ])
        ], className='two.columns')
    ], className='row')

app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=True)