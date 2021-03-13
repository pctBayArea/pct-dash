#!/usr/bin/python3

import json
import numpy as np
import pandas as pd
import geopandas as gpd
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
import dash_leaflet.express as dlx
import dash_bootstrap_components as dbc
import dash 
from dash.dependencies import Output, Input
from dash_extensions.javascript import arrow_function
from dash_extensions.javascript import Namespace, arrow_function

from shapely.geometry import Point, LineString


def get_info(case, feature=None):
    if (case == "acs"):
        header = [html.H4("Bay Area commute trips (ACS 2011-2015)")]
    else:
        header = [html.H4("Bay Area commute trips (go Dutch!)")]
    if not feature:
        return header + ["Hoover over the map"]

    feature = json.loads(feature)
    return header + [html.B(feature["name"]), html.Br(),
                     html.Table([
                        html.Tr([html.Td("{:.0f} ".format(feature["all"])       , style={'text-align': 'right'}), html.Td("total trips per day")]),
                        html.Tr([html.Td("{:.0f}%".format(feature[get_data(case)]*100.0), style={'text-align': 'right'}), html.Td("by bike")]),
                     ]),
                    ]

def get_url_fg(zoomed, region, feature):
    if (zoomed):
        if (region == 'cnt'):
            url="assets/commute/county/"+feature+"/taz.pbf"  # url to geojson file
        elif (region == 'plc'):
            url="assets/commute/place/"+feature+"/taz.pbf"  # url to geojson file
    else:
        if (region == 'cnt'):
            url="assets/commute/bayArea_county.pbf"  # url to geojson file
        elif (region == 'plc'):
            url="assets/commute/bayArea_place.pbf"  # url to geojson file
    
    return url


def get_url_bg(zoomed, region, feature):
    if (zoomed):
        if (region == 'cnt'):
            url="assets/commute/county/"+feature+"/county.pbf"  # url to geojson file
        elif (region == 'plc'):
            url="assets/commute/place/"+feature+"/place.pbf"  # url to geojson file
    else:
        if (region == 'cnt'):
            url=None
        elif (region == 'plc'):
            url=None

    return url

def get_data(case):
    if (case == "acs"):
        return "bike"
    else:    
        return "go_dutch"

def get_data_lines(zoomed, region, case, nlines, feature):
    if (zoomed):
        if (region == 'cnt'):
            fd = pd.read_pickle("assets/commute/county/"+feature+"/line.pkl")
            fd = fd.nlargest(nlines, get_data(case))
            fd = fd.loc[fd[get_data(case)] > 1.0]
            data = fd.to_crs("EPSG:4326").to_json(drop_id=True)
            data = json.loads(data)
        elif (region == 'plc'):
            fd = pd.read_pickle("assets/commute/place/"+feature+"/line.pkl")
            fd = fd.nlargest(nlines, get_data(case))
            fd = fd.loc[fd[get_data(case)] > 1.0]
            data = fd.to_crs("EPSG:4326").to_json(drop_id=True)
            data = json.loads(data)
    else:
        data=None

    return data

classes = [-0.0000001, 0.01, 0.02, 0.04, 0.08, 0.15, 0.20, 0.25, 0.30, 0.40]
colorscale = ['#BE4B65', '#E36E68', '#F69779', '#FDC690', '#FEE9B1', '#FBFCCF', '#D6E5F3', '#C4E4EF', '#9EC5DF', '#7C9DC9']
style = dict(weight=2, opacity=1, color='white', dashArray='3', fillOpacity=0.7)

def get_hideout(case):        
    if (case == "acs"):
        return dict(colorscale=colorscale, classes=classes, style=style, colorProp="bike")
    else:
        return dict(colorscale=colorscale, classes=classes, style=style, colorProp="go_dutch")

# Create colorbar.
ctg = ["{:.0f}%+".format(np.abs(cls*100), classes[i + 1]) for i, cls in enumerate(classes[:-1])] + ["{:.0f}%+".format(classes[-1]*100)]
colorbar = dlx.categorical_colorbar(categories=ctg, colorscale=colorscale, width=500, height=30, position="bottomleft")


dd_region = dcc.Dropdown(options=[
    {'label': 'Places', 'value': 'plc'},
    {'label': 'Counties', 'value': 'cnt'}
], value='cnt', id="dd_region", clearable=False, searchable=False, style={"opacity": "1.0"})

dd_case = dcc.Dropdown(options=[
    {'label': 'ACS 2011-2015', 'value': 'acs'},
    {'label': 'Go Dutch!', 'value': 'go_dutch'}
], value='acs', id="dd_case", clearable=False, searchable=False, style={"opacity": "1.0"})

default_zoomed = False
default_region = 'cnt'
default_case = "acs"
default_nlines = 0.0
default_name = None

def disable_odlines(zoomed):
    if (zoomed):
        return False
    else:
        return True

sl_line = dcc.Slider(
    min=0,
    max=50,
    value=0,
    step=1.0,
    marks={
         0: '0' ,
        10: '10',
        20: '20',
        30: '30',
        40: '40',
        50: '50'
    },
    disabled=disable_odlines(default_zoomed),
    id="sl_line",
)

# Create geojson foreground.
ns = Namespace("dlx", "choropleth")
geojson_fg = dl.GeoJSON(
    url=get_url_fg(default_zoomed, default_region, default_name),  # url to geojson file
    format="geobuf",
    options=dict(style=ns("style")),  # how to style each polygon
    hideout=get_hideout(default_case),
    zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature (e.g. polygon) on click
    hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray='')),  # style applied on hover
    id="geojson_fg"
)


# Create geojson background.
style = dict(weight=2, opacity=1, color='white', dashArray='3', fillOpacity=0.5)
geojson_bg = dl.GeoJSON(
    url=get_url_bg(default_zoomed, default_region, default_name),  # url to geojson file
    format="geobuf",
    options=dict(style=style),  # how to style each polygon
    zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature (e.g. polygon) on click
    hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray='')),  # style applied on hover
    id="geojson_bg"
)

# Create geojson od lines.
geojson_lines = dl.GeoJSON(
    data=get_data_lines(default_zoomed, default_region, default_case, default_nlines, default_name),  # url to geojson file
    options=dict(style=dict(color='blue', weight=3, opacity=1.0, fillOpacity=1.0)),  # how to style each polygon
    id="geojson_lines"
)

# Create info control.
info = html.Div(get_info(default_case), id="info", className="info", style={"position": "absolute", "top": "10px", "right": "10px", "z-index": "1000", "width": "284px", "height": "75px"})
regions = html.Div([dd_region], style={"position": "absolute", "top": "110px", "right": "18px", "z-index": "1000", "width": "300px", "opacity": "0.7"})
cases = html.Div([dd_case], style={"position": "absolute", "top": "153px", "right": "18px", "z-index": "900", "width": "300px", "opacity": "0.7"})
odlines = html.Div([html.B("Number of OD lines"), html.Br(), html.Br(), sl_line], id="odlines", className="info", style={"position": "absolute", "top": "195px", "right": "18px", "z-index": "800", "width": "282px", "opacity": "0.7"})

url = 'https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png'
attribution = '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> '

# Create app.
app = dash.Dash(prevent_initial_callbacks=True)
app = dash.Dash()
app.layout = html.Div(
    [
        dl.Map(center=[37.871667, -122.272778], zoom=8, children=[
            dl.TileLayer(url=url, maxZoom=20, attribution=attribution), 
            geojson_fg, 
            geojson_bg, 
            geojson_lines, 
            colorbar, 
            info,
        ]),
        regions,
        cases,
        odlines,
        html.Div(id='click-value', style={'display': 'none'}),
        html.Div(id='hover-value', style={'display': 'none'}),
        html.Div(id='zoom-value', style={'display': 'none'}),
    ],
    style={'width': '100%', 'height': '97vh', 'margin': "auto", "display": "block"}, id="map",
)

@app.callback(Output("zoom-value", "children"), [Input("dd_region", "value"), Input("geojson_fg", "click_feature"), Input("geojson_bg", "click_feature")])
def zoomed(region,click_fg, click_bg):
    ctx = dash.callback_context

    if (ctx.triggered[0]["prop_id"] == "geojson_fg.click_feature" or ctx.triggered[0]["prop_id"] == "geojson_bg.click_feature"):    
        return True

    if (ctx.triggered[0]["prop_id"] == "dd_region.value"):
        return False


@app.callback(Output("click-value", "children"), [Input("geojson_fg", "click_feature"), Input("geojson_bg", "click_feature")])
def clicking(click_fg, click_bg):
    ctx = dash.callback_context

    if (ctx.triggered[0]["prop_id"] == "geojson_fg.click_feature"):    
        return click_fg["properties"]["name"].replace(" ","")

    if (ctx.triggered[0]["prop_id"] == "geojson_bg.click_feature"):
        return click_bg["properties"]["name"].replace(" ","")


@app.callback(Output("hover-value", "children"), [Input("geojson_fg", "hover_feature"), Input("geojson_bg", "hover_feature")])
def hovering(hover_fg, hover_bg):
    ctx = dash.callback_context

    if (ctx.triggered[0]["prop_id"] == "geojson_fg.hover_feature"):
        if (hover_fg):
            return json.dumps(hover_fg["properties"])
        
    if (ctx.triggered[0]["prop_id"] == "geojson_bg.hover_feature"):
        if (hover_bg):
            return json.dumps(hover_bg["properties"])


@app.callback([
    Output("info", "children"), 
    Output("geojson_fg", "hideout"), 
    Output("geojson_fg", "url"), 
    Output("geojson_bg", "url"),
    Output("geojson_lines", "data"),
    Output("sl_line", "disabled"), 
], [
    Input("zoom-value", "children"),
    Input("dd_region", "value"),
    Input("dd_case", "value"),
    Input("sl_line", "value"),
    Input("click-value", "children"),
    Input("hover-value", "children")
])
def update_map(zoomed, region, case, nlines, click, hover):
    ctx = dash.callback_context

    if (ctx.triggered[0]["prop_id"] == "geojson_fg.click_feature" or ctx.triggered[0]["prop_id"] == "geojson_bg.click_feature"):
        clicked = True
    else:    
        clicked = False

    return get_info(case, hover), get_hideout(case), get_url_fg(zoomed, region, click), get_url_bg(zoomed, region, click), get_data_lines(zoomed, region, case, nlines, click), disable_odlines(zoomed)


if __name__ == '__main__':
    app.run_server(debug=True)
