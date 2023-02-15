import logging
import re
import webbrowser
from time import time

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dcc
from hakai_api import Client

logger = logging.getLogger(__name__)


def parse_hakai_token(token):
    return dict(item.split("=") for item in token.split("&"))


hakai_api_credentials_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Hakai API Crendentials"), close_button=True),
        dbc.ModalBody(
            [
                dcc.Markdown(
                    """Please go here and authorize:\n\n https://hecate.hakai.org/api-client-login\n\nCopy and past your credentials from the login page:"""
                ),
                dcc.Input(
                    placeholder="token_type=...",
                    id="credentials-input",
                    type="text",
                    debounce=True,
                    persistence=True,
                    persistence_type="local",
                ),
            ]
        ),
    ],
    id="credentials-modal",
    centered=True,
    is_open=False,
)


@callback(Output("credentials-modal", "is_open"), Input("credentials", "data"))
def open_credential_modal(credentials):

    if credentials is None:
        webbrowser.open_new_tab("https://hecate.hakai.org/api-client-login")
        return True
    token = parse_hakai_token(credentials)
    return int(token["expires_at"]) < time()


@callback(Output("credentials", "data"), Input("credentials-input", "value"))
def apply_credentials(credentials):
    logger.debug(
        "apply_credentials: len(credentials) = %s",
        len(credentials) if isinstance(credentials, str) else "None",
    )
    return credentials


@callback(
    Output("dataframe", "data"),
    Input("location", "search"),
    Input("credentials", "data"),
)
def get_hakai_data(query, credentials):
    if not credentials or not query:
        return
    client = Client(credentials=credentials)

    url = f"{client.api_root}/{query[1:]}"
    logger.debug("run hakai query: %s", url)

    response = client.get(url)
    if response.status_code == 200:
        result = response.json()
        logger.debug("result: %s", pd.DataFrame(result).head())
        return response.json()
    logger.debug("failed hakai query: %s", response.status_code)
