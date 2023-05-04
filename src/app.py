# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import logging
import os

import dash_bootstrap_components as dbc
import plotly.io as pio
import sentry_sdk
from dash import Dash, Input, Output, State, callback, dcc, html
from sentry_sdk.integrations.logging import LoggingIntegration

import selection as selection
from hakai_plotly_template import hakai_template
from utils import load_config

from download_hakai import hakai_api_credentials_modal
from navbar import navbar, data_filter_interface
from tooltips import tooltips
from figure import figure_menu, figure_radio_buttons

# load hakai template
pio.templates["hakai"] = hakai_template
pio.templates.default = "hakai"

config = load_config()
config.update({key: value for key, value in os.environ.items() if key in config})
if not os.path.exists(config["TEMP_FOLDER"]):
    os.makedirs(config["TEMP_FOLDER"])

if config.get("ACTIVATE_SENTRY_LOG") in (True, "true", 1):
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


app.layout = html.Div(
    [
        navbar,
        data_filter_interface,
        figure_radio_buttons,
        figure_menu,
        dcc.Graph(id={"type": "graph", "page": "main"}, figure={}),
        selection.selection_interface,
        hakai_api_credentials_modal,
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
