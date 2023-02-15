# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import logging
import os

import dash
import dash_bootstrap_components as dbc
import sentry_sdk
import yaml
from dash import Dash, dcc, html
from dotenv import dotenv_values
from sentry_sdk.integrations.logging import LoggingIntegration

import utils.selection as selection
from utils.hakai import hakai_api_credentials_modal

# Load configuration
with open("default-config.yaml", encoding="UTF-8") as config_handle:
    config = yaml.load(config_handle, Loader=yaml.SafeLoader)
config.update(
    {
        **dotenv_values(".env"),  # load shared development variables
        **os.environ,  # override loaded values with environment variables
    }
)

config.update({key: value for key, value in os.environ.items() if key in config})

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
fileHandler = logging.FileHandler("dashboard.log")
fileHandler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
)
logger.addHandler(fileHandler)

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
                dbc.DropdownMenuItem("Show Selection", href="#", id="show-selection"),
                dbc.DropdownMenuItem("Setup", href="#"),
            ],
            nav=True,
            in_navbar=True,
            label="More",
        ),
    ],
    brand="Hakai Quality Control",
    brand_href="#",
    color=config['NAVBAR_COLOR'],
    dark=config["NAVBAR_DARK"],
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