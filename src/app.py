# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import logging
import os

import dash
import dash_bootstrap_components as dbc
import plotly.io as pio
import sentry_sdk
from dash import Dash, Input, Output, State, callback, dcc, html
from sentry_sdk.integrations.logging import LoggingIntegration

import utils.selection as selection
from utils import hakai
from utils.hakai_plotly_template import hakai_template
from utils.tools import load_config

from figure import *
from navbar import get_navbar
from tooltips import tooltips

# load hakai template
pio.templates["hakai"] = hakai_template
pio.templates.default = "hakai"

config = load_config()
config.update({key: value for key, value in os.environ.items() if key in config})
if not os.path.exists(config["TEMP_FOLDER"]):
    os.makedirs(config["TEMP_FOLDER"])

sentry_logging = LoggingIntegration(
    level=config["SENTRY_LEVEL"],  # Capture info and above as breadcrumbs
    event_level=config["SENTRY_EVENT_LEVEL"],  # Send errors as events
)
sentry_sdk.init(
    dsn=config["SENTRY_DSN"],
    integrations=[
        sentry_logging,
    ],
    traces_sample_rate=1.0,
)

logger = logging.getLogger()
logger.setLevel(config["LOG_LEVEL"])
fileHandler = logging.FileHandler("logs/dashboard.log")
fileHandler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
)
logger.addHandler(fileHandler)

app = Dash(
    config["APP_NAME"],
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    assets_folder="src/assets",
)


data_interface = dbc.Collapse(
    dbc.Card(
        [
            dbc.CardHeader("Filter data by"),
            dbc.CardBody(
                dbc.Row(id="dataframe-subsets", align="center", justify="center")
            ),
        ]
    ),
    id="data-selection-interface",
    className="data-selection-interface",
    is_open=False,
)


@callback(
    Output("data-selection-interface", "is_open"),
    Input("filter-by", "n_clicks"),
    Input("data-selection-interface", "is_open"),
)
def showfilter_by_section(n_clicks, is_in):
    return not is_in if n_clicks else False


@callback(
    Output("variable", "value"),
    State("variable", "value"),
    Input("variable", "options"),
)
def define_variable(value, options):
    if value:
        return value
    return options[0]["value"] if options else None


app.layout = html.Div(
    [
        get_navbar(config["NAVBAR_COLOR"], config["NAVBAR_DARK"]),
        data_interface,
        dbc.Row(
            [
                dbc.Col(plot_inputs, width=2),
                dbc.Col(
                    figure_radio_buttons,
                    className="radio-group col-5 mx-auto",
                ),
                dbc.Col(width=2),
            ]
        ),
        dcc.Graph(id={"type": "graph", "page": "nutrients"}, figure={}),
        selection.selection_interface,
        hakai.hakai_api_credentials_modal,
        dcc.Location(id="location"),
        html.Div(id="toast-container"),
        tooltips,
    ]
)

if __name__ == "__main__":
    app.run_server(
        host=config["DASH_HOST"],
        port=config["DASH_PORT"],
        debug=True
        if config["DASH_DEBUG"] not in (False, "false", "False", 0)
        else False,
    )
