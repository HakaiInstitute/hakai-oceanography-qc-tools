import os

### Import Packages ###
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State

### Import Dash Instance and Pages ###
import utils.selection as selection
from app import app
from pages import home, nutrients
from utils import hakai
from utils.tools import load_config

config = load_config()
config.update({key: value for key, value in os.environ.items() if key in config})

stores = html.Div(
    dbc.Spinner(
        [
            dcc.Store(id="dataframe"),
            dcc.Store(id="selected-data"),
            dcc.Store(id="main-graph-spinner"),
        ],
        color="light",
    ),
    style={"width": "50px", "float": "center", "text-align": "center"},
)

navbar = dbc.NavbarSimple(
    children=[
        stores,
        *[
            dbc.NavItem(dbc.NavLink(page["name"], href=page["relative_path"]))
            for page in dash.page_registry.values()
        ],
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Query", href="#query"),
                dbc.DropdownMenuItem(
                    "Show Selection", href="#selection", id="show-selection"
                ),
                dbc.DropdownMenuItem("Log In", id="log-in"),
            ],
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand="Hakai Quality Control",
    brand_href="#",
    color=config["NAVBAR_COLOR"],
    dark=config["NAVBAR_DARK"],
)

data_interface = dbc.Collapse(
    [
        dcc.Dropdown(id="variable", clearable=False, className="selection-box"),
        dcc.Dropdown(
            id="line-out-depth-selector",
            multi=True,
            className="selection-box",
            placeholder="line out depth(s)",
        ),
    ],
    id="data-selection-interface",
    className="data-selection-interface",
    is_open=True,
)


page_container = html.Div(
    children=[
        # represents the URL bar, doesn't render anything
        navbar,
        data_interface,
        dcc.Location(
            id="location",
            refresh=False,
        ),
        # content will be rendered in this element
        html.Div(id="page-content"),
    ]
)


### Index Page Layout ###
index_layout = html.Div(
    children=[
        dcc.Link(
            children="Review Nutrients",
            href="/nutrients",
        ),
    ]
)
### Set app layout to page container ###
app.layout = page_container
### Assemble all layouts ###
app.validation_layout = html.Div(
    children=[
        page_container,
        navbar,
        home.layout,
        nutrients.layout,
        selection.selection_interface,
        hakai.hakai_api_credentials_modal,
        dcc.Location(id="location"),
        html.Div(id="toast-container"),
    ]
)


### Update Page Container ###
@app.callback(
    Output(
        "page-content",
        "children",
    ),
    [
        Input(
            "location",
            "pathname",
        )
    ],
)
def display_page(pathname):
    if pathname == "/":
        return index_layout
    elif pathname == "/nutrients":
        return nutrients.layout
    else:
        return "404"


@app.callback(
    Output("variable", "value"),
    State("variable", "value"),
    Input("variable", "options"),
)
def define_variable(value, options):
    if value:
        return value
    return options[0]["value"] if options else None
