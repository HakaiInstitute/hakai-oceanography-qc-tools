# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import logging

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, State, dash_table, dcc, html

from utils.hakai import hakai_api_credentials_modal

logging.basicConfig(level=logging.DEBUG, filename="web_debug.log")
logger = logging.getLogger()

app = Dash(
    "Hakai Quality Control",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    use_pages=True,
    pages_folder="src/pages",
)
application = app.server


app.layout = html.Div(
    [
        html.H1(children="Hakai QC Tool"),
        dbc.Spinner(
            [
                dcc.Store(id="dataframe"),
                dcc.Store(id="credentials", storage_type="local"),
                dcc.Store(id="selected-data"),
                dcc.Store(id="main-graph-spinner"),
            ]
        ),
        html.Div(
            children="""
        Dash: A web application framework for your data.
    """
        ),
        html.Div(
            [
                html.Div(
                    dcc.Link(
                        page['name'], href=page["relative_path"]
                    )
                )
                for page in dash.page_registry.values()
            ]
        ),
        dash.page_container,
        dash_table.DataTable(id="selected-data-table"),
        hakai_api_credentials_modal,
        dcc.Location(id="location"),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
