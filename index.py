#!/usr/bin/python3

import json
#import numpy as np
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
import dash_leaflet.express as dlx
import dash_bootstrap_components as dbc
#from dash import Dash
import dash 
from dash.dependencies import Output, Input
from dash_extensions.javascript import arrow_function
from dash_extensions.javascript import Namespace, arrow_function

# What is the user interface I am looking for?
# Click on region zoomes in to TAZ
# Empy data for neighboring regions or colored data?

def get_info(feature=None):
    header = [html.H4("Bay Area commute trips (ACS 2011-2015)")]
    if not feature:
        return header + ["Hoover over the map"]

    feature = json.loads(feature)
    return header + [html.B(feature["NAME"]), html.Br(),
                     html.Table([
                        html.Tr([html.Td("{:.0f} ".format(feature["ALL"])       , style={'text-align': 'right'}), html.Td("total trips per day")]),
                        html.Tr([html.Td("{:.0f}%".format(feature["BIKE"]*100.0), style={'text-align': 'right'}), html.Td("by bike")]),
                        html.Tr([html.Td("{:.0f}%".format(feature["SOV"]*100.0) , style={'text-align': 'right'}), html.Td("by SOV")])
                     ]),
                    ]

def get_url_fg(zoomed, region, feature):
    if (zoomed):
        if (region == 'cnt'):
#            url="/assets/commute/county/"+feature+"/taz.GeoJson",  # url to geojson file
            url="/assets/commute/county/"+feature+"/taz.pbf",  # url to geojson file
        elif (region == 'plc'):
#            url="/assets/commute/place/"+feature+"/taz.GeoJson",  # url to geojson file
            url="/assets/commute/place/"+feature+"/taz.pbf",  # url to geojson file
    else:
        if (region == 'cnt'):
#            url="/assets/commute/bayArea_county.GeoJson",  # url to geojson file
            url="/assets/commute/bayArea_county.pbf",  # url to geojson file
        elif (region == 'plc'):
#            url="/assets/commute/bayArea_place.GeoJson",  # url to geojson file
            url="/assets/commute/bayArea_place.pbf",  # url to geojson file

    return url


def get_url_bg(zoomed, region, feature):
    if (zoomed):
        if (region == 'cnt'):
#            url="/assets/commute/county/"+feature+"/county.GeoJson",  # url to geojson file
            url="/assets/commute/county/"+feature+"/county.pbf",  # url to geojson file
        elif (region == 'plc'):
#            url="/assets/commute/place/"+feature+"/place.GeoJson",  # url to geojson file
            url="/assets/commute/place/"+feature+"/place.pbf",  # url to geojson file
    else:
        if (region == 'cnt'):
            url=None
        elif (region == 'plc'):
            url=None

    return url

classes = [-0.0000001, 0.01, 0.02, 0.04, 0.08, 0.15, 0.20, 0.25, 0.30, 0.40]
colorscale = ['#BE4B65', '#E36E68', '#F69779', '#FDC690', '#FEE9B1', '#FBFCCF', '#D6E5F3', '#C4E4EF', '#9EC5DF', '#7C9DC9']
style = dict(weight=2, opacity=1, color='white', dashArray='3', fillOpacity=0.7)

# Create colorbar.
ctg = ["{:.0f}%+".format(cls*100, classes[i + 1]) for i, cls in enumerate(classes[:-1])] + ["{:.0f}%+".format(classes[-1]*100)]
colorbar = dlx.categorical_colorbar(categories=ctg, colorscale=colorscale, width=500, height=30, position="bottomleft")

dd_region = dcc.Dropdown(options=[
    {'label': 'Places', 'value': 'plc'},
    {'label': 'Counties', 'value': 'cnt'}
], value='cnt', id="dd_region", clearable=False)

default_zoomed = False
default_region = 'cnt'
default_name = None

# Create geojson foreground.
ns = Namespace("dlx", "choropleth")
geojson_fg = dl.GeoJSON(
    url=get_url_fg(default_zoomed, default_region, default_name),  # url to geojson file
    format="geobuf",
    options=dict(style=ns("style")),  # how to style each polygon
    hideout=dict(colorscale=colorscale, classes=classes, style=style, colorProp="BIKE"),
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


# Create info control.
info = html.Div(children=get_info(), id="info", className="info",
                style={"position": "absolute", "top": "10px", "right": "10px", "z-index": "1000"})

url = 'https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png'
attribution = '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> '

# Create app.
app = dash.Dash(prevent_initial_callbacks=True)
app = dash.Dash()
app.layout = html.Div(
    [
#        navbar,
        dl.Map(center=[37.871667, -122.272778], zoom=8, children=[
#        dl.Map(center=[np.nan, np.nan], zoom=8, children=[
#        dl.Map(children=[
            dl.TileLayer(url=url, maxZoom=20, attribution=attribution), 
            geojson_fg, 
            geojson_bg, 
            colorbar, 
            info,
        ]),
        html.Div([dd_region],
        style={"position": "relative", "bottom": "80px", "left": "10px", "z-index": "1000", "width": "200px"}),
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
        return click_fg["properties"]["NAME"].replace(" ","")

    if (ctx.triggered[0]["prop_id"] == "geojson_bg.click_feature"):
        return click_bg["properties"]["NAME"].replace(" ","")


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
    Output("geojson_fg", "url"), 
    Output("geojson_bg", "url")
], [
    Input("zoom-value", "children"),
    Input("dd_region", "value"),
    Input("click-value", "children"),
    Input("hover-value", "children")
])
def update_map(zoomed, region, click, hover):
    ctx = dash.callback_context

    if (ctx.triggered[0]["prop_id"] == "geojson_fg.click_feature" or ctx.triggered[0]["prop_id"] == "geojson_bg.click_feature"):
        clicked = True
    else:    
        clicked = False

    return get_info(hover), get_url_fg(zoomed, region, click), get_url_bg(zoomed, region, click)

if __name__ == '__main__':
    app.run_server(debug=True)
