import folium
from folium.features import DivIcon

def create_map(clean_data):
    # Initialize variables
    geo_neighborhoods = clean_data[0]
    positive_cases_by_neighborhood_only_known_names = clean_data[1]
    positive_cases_no_information_neighborhoods = clean_data[2]
    deaths_no_information_neighborhoods = clean_data[3]
    positive_cases_total = clean_data[4]
    deaths_total = clean_data[5]

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

    map.save('Covid-19_confirmed_cases_fortaleza.html')