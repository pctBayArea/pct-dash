#!/usr/bin/python3

import dash_html_components as html
import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash import Dash
from dash.dependencies import Output, Input
from dash_extensions.javascript import arrow_function

#app = Dash()
#app.layout = html.Div([
#    dl.Map(center=[39, -98], zoom=4, children=[
#        dl.TileLayer(),
##        dl.GeoJSON(data=bermuda),  # in-memory geojson (slowest option)
##        dl.GeoJSON(data=biosfera, format="geobuf"),  # in-memory geobuf (smaller payload than geojson)
##        dl.GeoJSON(url="/assets/us-state-capitals.json", id="capitals"),  # geojson resource (faster than in-memory)
##        dl.GeoJSON(url="/assets/us-states.pbf", format="geobuf", id="states",
##                   hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray=''))),  # geobuf resource (fastest option)
#    ], style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"}, id="map"),
##    html.Div(id="state"), html.Div(id="capital")
#])

