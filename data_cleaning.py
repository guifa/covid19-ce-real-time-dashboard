import pandas as pd
import utils

# Remove .loc warning s
pd.options.mode.chained_assignment = None

def clean_data(data, geo_data):
    # Rename columns
    data.columns = ['bairroPaciente', 'classificacaoEstadoSivep', 'codigoMunicipioPaciente','codigoPaciente', 'comorbidadeAsmaSivep', 'comorbidadeCardiovascularSivep', 'comorbidadeDiabetesSivep', 
                        'comorbidadeHematologiaSivep', 'comorbidadeImunodeficienciaSivep', 'comorbidadeNeurologiaSivep', 'comorbidadeObesidadeSivep', 'comorbidadePneumopatiaSivep', 'comorbidadePuerperaSivep', 
                        'comorbidadeRenalSivep', 'comorbidadeSindromedownSivep', 'dataColetaExame', 'dataEntradaUtisSivep', 'dataEvolucaoCasoSivep', 'dataInicioSintomas', 'dataInternacaoSivep', 'dataNotificacao', 
                        'dataObito', 'dataResultadoExame', 'dataSaidaUtisSivep', 'dataSolicitacaoExame',  'estadoPaciente', 'evolucaoCasoSivep', 'idadePaciente', 'idSivep', 'municipioPaciente', 'obitoConfirmado', 
                        'paisPaciente', 'resultadoFinalExame', 'sexoPaciente']

    # Convert string to datetime
    data['dataNotificacao'] = pd.to_datetime(data['dataNotificacao'], errors='coerce')
    data['dataInicioSintomas'] = pd.to_datetime(data['dataInicioSintomas'], errors='coerce')
    data['dataColetaExame'] = pd.to_datetime(data['dataColetaExame'], errors='coerce')
    data['dataResultadoExame'] = pd.to_datetime(data['dataResultadoExame'], errors='coerce')

    # Selecting rows of the city Fortaleza
    data = data[(data['municipioPaciente'] == 'FORTALEZA')]

    # Get only positive results
    data = data[(data['resultadoFinalExame'] == 'Positivo')]

    # Remove duplicate codes keeping the first appearance
    data = data.sort_values('bairroPaciente').drop_duplicates(subset='codigoPaciente', keep='first')

    # Remove NaNs from neighborhoods
    data['bairroPaciente'].fillna('NAO INFORMADO', inplace=True)

    # Clean neighborhoods names
    data['bairroPaciente'] = data['bairroPaciente'].map(utils.clean_text)

    # Get official neighborhoods names
    official_neighborhoods_names = geo_data['NOME'].tolist()

    # For each row it will compare the name of the row neighborhood to the official list and pick the closest name based on the minimum edit distance
    data['bairroPaciente'] = data['bairroPaciente'].apply(utils.min_edit_distance, list_of_words = official_neighborhoods_names)

    positive_cases_by_neighborhood = data.groupby('bairroPaciente').count()['codigoPaciente']

    # Get positive cases of rows with neighborhood information
    positive_cases_by_neighborhood_only_known_names = data[data['bairroPaciente'] != 'NAO INFORMADO'].groupby('bairroPaciente').count()['codigoPaciente']

    # Get positive cases of rows with no neighborhood information
    positive_cases_no_information_neighborhoods = data[data['bairroPaciente'] == 'NAO INFORMADO'].count()['codigoPaciente']

    positive_cases_total = data['codigoPaciente'].count()

    deaths_by_neighborhood = data[data['obitoConfirmado'] == True].groupby('bairroPaciente').count()['codigoPaciente']

    # Get deaths of rows with no neighborhood information
    deaths_no_information_neighborhoods = data[(data['obitoConfirmado'] == True) & (data['bairroPaciente'] == 'NAO INFORMADO')].count()['codigoPaciente']

    deaths_total = data[data['obitoConfirmado'] == True].count()['codigoPaciente']

    # Merge geo_data and positive_cases_by_neighborhood
    geo_data = pd.merge(left=geo_data, right=positive_cases_by_neighborhood, left_on='NOME', right_on='bairroPaciente', how='left')
    geo_data.rename(columns={'codigoPaciente': 'CASOS_POSITIVOS'}, inplace=True)
    geo_data['CASOS_POSITIVOS'].fillna(0, inplace=True)

    # Merge geo_data and deaths_by_neighborhood
    geo_data = pd.merge(left=geo_data, right=deaths_by_neighborhood, left_on='NOME', right_on='bairroPaciente', how='left')
    geo_data.rename(columns={'codigoPaciente': 'OBITOS_CONFIRMADOS'}, inplace=True)
    geo_data['OBITOS_CONFIRMADOS'].fillna(0, inplace=True)

    # Convert to WGS84
    geo_data = geo_data.to_crs(epsg=4326).to_json()

    return geo_data, positive_cases_by_neighborhood_only_known_names, positive_cases_no_information_neighborhoods, deaths_no_information_neighborhoods, positive_cases_total, deaths_total