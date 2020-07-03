from datetime import datetime
import dash
import dash_html_components as html
from rq import Queue
from worker import conn

import data
import data_cleaning
import map

queue = Queue(connection=conn)

def serve_layout():
    return html.Div([
        html.Div([
            html.H2(f'Casos confirmados de Covid-19 em Fortaleza-CE - Atualizado: {datetime.now().strftime("%d/%m/%Y")}'),
            html.A('Github onde está hospedado o código.', href='https://github.com/guifa/covid19-ce-real-time-dashboard'),
            html.Iframe(id='map', srcDoc=open('Covid-19_confirmed_cases_fortaleza.html', 'r').read(), width='800', height='800', className='iframe')
        ], className='two.columns')
    ], className='row')

def job():
    # Get required data
    covid_cases = data.getCovidCases()
    geo_neighborhoods = data.getGeoData()
    
    # Clean data
    clean_data = data_cleaning.clean_data(covid_cases, geo_neighborhoods)
    
    # Create map
    map.create_map(clean_data)

queue.enqueue(job)

# Create app
app = dash.Dash(__name__)

server = app.server

app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=False)