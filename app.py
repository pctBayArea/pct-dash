#!/usr/bin/python3

import os
from urllib.parse import urljoin
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import dash 
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
import dash_leaflet.express as dlx
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input
from dash_extensions.javascript import arrow_function
from dash_extensions.javascript import Namespace, arrow_function
from whitenoise import WhiteNoise

################################################################################
# Default values
################################################################################

#base_url = "http://127.0.0.1:8050/" # Running locally
base_url = "https://pctbayarea.herokuapp.com/" # Running on heroku

default_zoomed = False
default_region = "cnt"
default_case = "acs"
default_nlines = 0.0
default_name = None

url = 'https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png'
attribution = '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> '

classes = [-0.0000001, 0.01, 0.02, 0.04, 0.08, 0.15, 0.20, 0.25, 0.30, 0.40]
colorscale = ['#BE4B65', '#E36E68', '#F69779', '#FDC690', '#FEE9B1', '#FBFCCF', 
    '#D6E5F3', '#C4E4EF', '#9EC5DF', '#7C9DC9']

################################################################################
# Helper functions
################################################################################

def get_data(case):
    if (case == "acs"):
        return "bike"
    else:    
        return "go_dutch"

style_hideout = {"weight": 2, "opacity": 1, "color": "white", "dashArray": 3,
    "fillOpacity": 0.7}
def get_hideout(case):        
    if (case == "acs"):
        return dict(colorscale=colorscale, classes=classes, 
            style=style_hideout, colorProp="bike")
    else:
        return dict(colorscale=colorscale, classes=classes, 
            style=style_hideout, colorProp="go_dutch")

def disable_odlines(zoomed):
    if (zoomed):
        return False
    else:
        return True

def fast_scandir(dirname):
    subfolders= [f.path for f in os.scandir(dirname) if f.is_dir()]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders

################################################################################
# Create elements
################################################################################

# Create colorbar.
ctg = ["{:.0f}%+".format(np.abs(cls*100), classes[i + 1]) 
    for i, cls in enumerate(classes[:-1])] + [
    "{:.0f}%+".format(classes[-1]*100)]
colorbar = dlx.categorical_colorbar(categories=ctg, colorscale=colorscale, 
    width=500, height=30, position="bottomleft")

style_table={"text-align": "right"}
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
            html.Tr([html.Td("{:.0f} ".format(feature["all"]), 
            style=style_table), html.Td("total trips per day")]),
            html.Tr([html.Td("{:.0f}%".format(feature[get_data(case)]*100.0), 
            style=style_table), html.Td("by bike")])])]

def get_url_fg(zoomed, region, feature):
    if (zoomed):
        if (region == 'cnt'):
            url="/assets/commute/county/"+feature+"/taz.pbf"  # url to geojson file
        elif (region == 'plc'):
            url="/assets/commute/place/"+feature+"/taz.pbf"  # url to geojson file
    else:
        if (region == 'cnt'):
            url="/assets/commute/bayArea_county.pbf"  # url to geojson file
        elif (region == 'plc'):
            url="/assets/commute/bayArea_place.pbf"  # url to geojson file
    
    return url

def get_url_bg(zoomed, region, feature):
    if (zoomed):
        if (region == 'cnt'):
            url="/assets/commute/county/"+feature+"/county.pbf"  # url to geojson file
        elif (region == 'plc'):
            url="/assets/commute/place/"+feature+"/place.pbf"  # url to geojson file
    else:
        if (region == 'cnt'):
            url=None
        elif (region == 'plc'):
            url=None

    return url

def get_data_lines(zoomed, region, case, nlines, feature):
    if (zoomed):
        if (region == 'cnt'):
            pickle = urljoin(base_url, "/assets/commute/county/"+feature+"/line.pkl")
            fd = pd.read_pickle(pickle)
            fd = fd.nlargest(nlines, get_data(case))
            fd = fd.loc[fd[get_data(case)] > 1.0]
            data = fd.to_crs("EPSG:4326").to_json(drop_id=True)
            data = json.loads(data)
        elif (region == 'plc'):
            pickle = urljoin(base_url, "/assets/commute/place/"+feature+"/line.pkl")
            fd = pd.read_pickle(pickle)
            fd = fd.nlargest(nlines, get_data(case))
            fd = fd.loc[fd[get_data(case)] > 1.0]
            data = fd.to_crs("EPSG:4326").to_json(drop_id=True)
            data = json.loads(data)
    else:
        data=None

    return data

################################################################################
# Webapp elements
################################################################################

dd_region = dcc.Dropdown(options=[
    {'label': 'Places', 'value': 'plc'},
    {'label': 'Counties', 'value': 'cnt'}
], value='cnt', id="dd_region", clearable=False, searchable=False)

dd_case = dcc.Dropdown(options=[
    {'label': 'ACS 2011-2015', 'value': 'acs'},
    {'label': 'Go Dutch!', 'value': 'go_dutch'}
], value='acs', id="dd_case", clearable=False, searchable=False)

sl_line = dcc.Slider(
    min=0,
    max=50,
    value=0,
    step=1.0,
    marks={
         0: "0" ,
        10: "10",
        20: "20",
        30: "30",
        40: "40",
        50: "50"
    },
    disabled=disable_odlines(default_zoomed),
    id="sl_line",
)

# Create geojson foreground.
style_hover = {"weight": 5, "color": "#666", "dashArray": ""}
ns = Namespace("dlx", "choropleth")
geojson_fg = dl.GeoJSON(
    url=get_url_fg(default_zoomed, default_region, default_name),
    format="geobuf",
    options=dict(style=ns("style")),  # how to style each polygon
    hideout=get_hideout(default_case),
    zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature on click
    hoverStyle=arrow_function(style_hover),
    id="geojson_fg"
)

# Create geojson background.
style_bg = {"weight": 2, "opacity": 1, "color": "white", "dashArray": 3,
"fillOpacity": 0.5}
geojson_bg = dl.GeoJSON(
    url=get_url_bg(default_zoomed, default_region, default_name),
    format="geobuf",
    options=dict(style=style_bg),  # how to style each polygon
    zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature on click
    hoverStyle=arrow_function(style_hover),
    id="geojson_bg"
)

# Create geojson od lines.
style_lines = {"color": "blue", "weight": 3, "opacity": 1.0, 
    "fillOpacity": 1.0}
geojson_lines = dl.GeoJSON(
    data=get_data_lines(default_zoomed, default_region, default_case, 
        default_nlines, default_name),
    options=dict(style=style_lines), # how to style each line
    id="geojson_lines"
)

# Create controls
style_info = {"position": "absolute", "top": "10px", "right": "10px",
    "z-index": "1000", "width": "284px", "height": "75px"}
info = html.Div(get_info(default_case), id="info", className="info", 
    style=style_info)

style_regions = {"position": "absolute", "top": "110px", "right": "18px",
    "z-index": "1000", "width": "300px", "opacity": "0.7"} 
regions = html.Div([dd_region], style=style_regions)

style_cases = {"position": "absolute", "top": "153px", "right": "18px",
    "z-index": "900", "width": "300px", "opacity": "0.7"}
cases = html.Div([dd_case], style=style_cases)

style_odlines = {"position": "absolute", "top": "195px", "right": "18px",
    "z-index": "800", "width": "282px", "opacity": "0.7"}
odlines = html.Div([html.B("Number of OD lines"), html.Br(), html.Br(), 
    sl_line], id="odlines", className="info", style=style_odlines)

################################################################################
# Create app.
################################################################################

app = dash.Dash(prevent_initial_callbacks=True)
server = app.server
server.wsgi_app = WhiteNoise(
    server.wsgi_app,
    root=os.path.join(os.path.dirname(__file__), "static"),
    prefix="assets/",
)

# Loop through directories
subfolders = fast_scandir("static")

# Add them to whitenoise
for folder in subfolders:
    server.wsgi_app.add_files(os.path.join(os.path.dirname(__file__), folder))

style_none = {"display": "none"}
style_map = {"width": "100%", "height": "97vh", "margin": "auto", 
    "display": "block"}
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
        html.Div(id='click-value', style=style_none),
        html.Div(id='hover-value', style=style_none),
        html.Div(id='zoom-value', style=style_none),
    ],
    style=style_map, id="map",
)

################################################################################
# Callback
################################################################################

@app.callback(
    Output("zoom-value", "children"),
[
    Input("dd_region", "value"), 
    Input("geojson_fg", "click_feature"), 
    Input("geojson_bg", "click_feature")
])
def zoomed(region,click_fg, click_bg):
    ctx = dash.callback_context

    if (ctx.triggered[0]["prop_id"] == "geojson_fg.click_feature" 
            or ctx.triggered[0]["prop_id"] == "geojson_bg.click_feature"):    
        return True

    if (ctx.triggered[0]["prop_id"] == "dd_region.value"):
        return False

@app.callback(
    Output("click-value", "children"), 
[
    Input("geojson_fg", "click_feature"), 
    Input("geojson_bg", "click_feature")
])
def clicking(click_fg, click_bg):
    ctx = dash.callback_context

    if (ctx.triggered[0]["prop_id"] == "geojson_fg.click_feature"):
        click_value = click_fg["properties"]["name"].replace(" ","")
        if (click_value.isdigit()):
            raise PreventUpdate
        else:
            return click_value
    elif (ctx.triggered[0]["prop_id"] == "geojson_bg.click_feature"):
        return click_bg["properties"]["name"].replace(" ","")

@app.callback(
    Output("hover-value", "children"), 
[
    Input("geojson_fg", "hover_feature"), 
    Input("geojson_bg", "hover_feature")
])
def hovering(hover_fg, hover_bg):
    ctx = dash.callback_context

    if (ctx.triggered[0]["prop_id"] == "geojson_fg.hover_feature"):
        if (hover_fg):
            return json.dumps(hover_fg["properties"])
    elif (ctx.triggered[0]["prop_id"] == "geojson_bg.hover_feature"):
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

    if (ctx.triggered[0]["prop_id"] == "geojson_fg.click_feature" 
            or ctx.triggered[0]["prop_id"] == "geojson_bg.click_feature"):
        clicked = True
    else:    
        clicked = False

    return (get_info(case, hover), get_hideout(case), 
        get_url_fg(zoomed, region, click), get_url_bg(zoomed, region, click), 
        get_data_lines(zoomed, region, case, nlines, click), 
        disable_odlines(zoomed))

################################################################################

if __name__ == '__main__':
    app.run_server()
#    app.run_server(debug=True)

################################################################################
