# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import os

import click
import dash_bootstrap_components as dbc
import plotly.io as pio
import sentry_sdk
from dash import Dash, Input, Output, callback, dcc, html
from sentry_sdk.integrations.loguru import LoguruIntegration
from dotenv import load_dotenv

import hakai_qc_app.selection as selection
from hakai_qc_app.download_hakai import hakai_api_credentials_modal
from hakai_qc_app.figure import figure_menu, figure_radio_buttons
from hakai_qc_app.hakai_plotly_template import hakai_template
from hakai_qc_app.navbar import data_filter_interface, navbar
from hakai_qc_app.tooltips import tooltips
from hakai_qc_app.welcome import welcome_section

# load hakai template
pio.templates["hakai"] = hakai_template
pio.templates.default = "hakai"

load_dotenv()

sentry_sdk.init(
    dsn="https://f75b498b33164cc7bcf827f18f763435@o56764.ingest.sentry.io/4504520655110144",
    integrations=[
        LoguruIntegration(),
    ],
    environment=os.getenv("ENVIRONMENT",'local'),
    server_name=os.uname()[1],
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

app = Dash(
    "Hakai Data Viewer",
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],
    assets_folder="./hakai_qc_app/assets"
)

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

@click.command()
@click.option('--host', default="0.0.0.0", type=str, envvar='HOST')
@click.option('--port', default=8050, type=int, envvar='PORT')
@click.option("--debug", is_flag=True, show_default=True, default=True, envvar="DEBUG")
def run_app(host,port,debug=True):
    app.run_server(
        host=host,
        port=port,
        debug=debug,
    )


if __name__ == "__main__":
    run_app()
