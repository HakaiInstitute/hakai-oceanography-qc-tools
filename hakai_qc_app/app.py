# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import os

import dash_bootstrap_components as dbc
import plotly.io as pio
import sentry_sdk
from dash import Dash, Input, Output, callback, dcc, html
from loguru import logger
from sentry_sdk.integrations.loguru import LoguruIntegration

import hakai_qc_app.selection as selection
from hakai_qc_app.download_hakai import hakai_api_credentials_modal
from hakai_qc_app.figure import figure_menu, figure_radio_buttons
from hakai_qc_app.hakai_plotly_template import hakai_template
from hakai_qc_app.navbar import data_filter_interface, navbar
from hakai_qc_app.tooltips import tooltips
from hakai_qc_app.utils import load_config
from hakai_qc_app.welcome import welcome_section

# load hakai template
pio.templates["hakai"] = hakai_template
pio.templates.default = "hakai"

config = load_config()
config.update({key: value for key, value in os.environ.items() if key in config})
if not os.path.exists(config["TEMP_FOLDER"]):
    os.makedirs(config["TEMP_FOLDER"])

if config.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=config["SENTRY_DSN"],
        integrations=[
            LoguruIntegration(),
        ],
        environment=config["ENVIRONMENT"],
        server_name=os.uname()[1],
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )


logger.add("logs/dashboard.log", level="WARNING")

app = Dash(
    config["APP_NAME"],
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    assets_folder="hakai_qc_app/assets",
)
app.title = config["APP_NAME"]
app._favicon = "hakai_icon.png"

app.layout = html.Div(
    [
        navbar,
        hakai_api_credentials_modal,
        dbc.Collapse(
            [
                data_filter_interface,
                figure_radio_buttons,
                figure_menu,
                dcc.Graph(id={"type": "graph", "page": "main"}, figure={}),
                selection.qc_section,
            ],
            id="hide-all-figure-area",
            is_open=False,
        ),
        welcome_section,
        dcc.Location(id="location"),
        html.Div(id="toast-container"),
        tooltips,
    ]
)


@callback(
    Output("hide-all-figure-area", "is_open"),
    Input({"type": "graph", "page": "main"}, "figure"),
)
def show_figure_area(figure):
    return bool(figure)


if __name__ == "__main__":
    app.run_server(
        host=config["DASH_HOST"],
        port=config["DASH_PORT"],
        debug=True
        if config["DASH_DEBUG"] not in (False, "false", "False", 0)
        else False,
    )
