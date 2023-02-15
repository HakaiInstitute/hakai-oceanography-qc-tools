# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import logging

import dash
import dash_bootstrap_components as dbc
from dash import Dash, dash_table, dcc, html

from utils.hakai import hakai_api_credentials_modal
import utils.selection as selection

logging.basicConfig(level=logging.DEBUG, filename="web_debug.log")
logger = logging.getLogger()

app = Dash(
    "Hakai Quality Control",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    use_pages=True,
    pages_folder="src/pages",
)
application = app.server
stores = html.Div(
    dbc.Spinner(
        [
            dcc.Store(id="dataframe"),
            dcc.Store(id="credentials", storage_type="local"),
            dcc.Store(id="selected-data"),
            dcc.Store(id="main-graph-spinner"),
        ]
    )
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
                dbc.DropdownMenuItem("Query", href="#"),
                dbc.DropdownMenuItem("Show Selection", href="#", id='show-selection'),
                dbc.DropdownMenuItem("Setup", href="#"),
            ],
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand="Hakai Quality Control",
    brand_href="#",
    color="primary",
    dark=True,
)

app.layout = html.Div(
    [
        navbar,
        dbc.Label("Primary Variable"),
        dbc.Select(options=["sio2", "po4", "no2_no3_um"], value="sio2", id="variable"),
        dash.page_container,
        selection.selection_interface,
        hakai_api_credentials_modal,
        dcc.Location(id="location"),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
