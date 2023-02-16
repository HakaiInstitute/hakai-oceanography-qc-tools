import logging
import re
import webbrowser
from time import time
import json

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dcc, html, ctx
from hakai_api import Client

logger = logging.getLogger(__name__)


def parse_hakai_token(token):
    if token is None:
        return {"expires_at": 0}
    parsed_token = dict(item.split("=") for item in token.split("&"))
    parsed_token["expires_at"] = int(parsed_token["expires_at"])
    return parsed_token


location_endpoint_mapping = {"/nutrients": "eims/views/output/nutrients"}

hakai_api_credentials_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Hakai API Crendentials"), close_button=True),
        dbc.ModalBody(
            [
                "Please go here and authorize:\n",
                html.Br(),
                dcc.Link(
                    "https://hecate.hakai.org/api-client-login",
                    href="https://hecate.hakai.org/api-client-login",
                    target="_blank",
                ),
                html.Br(),
                html.Br(),
                "\nCopy and past your credentials from the login page:\n",
                dbc.Input(
                    placeholder="token_type=...",
                    id="credentials-input",
                    type="text",
                    debounce=True,
                    persistence=True,
                    persistence_type="local",
                    className="crendentials-input",
                ),
                dcc.Store(id="credentials", storage_type="local"),
            ]
        ),
    ],
    id="credentials-modal",
    centered=True,
    is_open=True,
)


@callback(
    Output("credentials", "data"),
    Output("credentials-modal", "is_open"),
    Input("credentials-modal", "is_open"),
    Input("credentials-input", "value"),
    Input("credentials", "data"),
    Input("log-in", "n_clicks"),
)
def apply_credentials(modal_open, credentials_input, credentials_stored, log_in_clicks):
    def _test_hakai_api_credentials(creds):
        if creds is None:
            return False
        try:
            Client(credentials=creds)
            return True
        except Exception as e:
            # logger('token test failed: %s', e)
            return False

    triggered_id = ctx.triggered_id
    if triggered_id == "log-in":
        logger.debug("clicked on log-in")
        return credentials_stored, not modal_open

    stored_credentials_test = _test_hakai_api_credentials(credentials_stored)
    input_credentials_test = _test_hakai_api_credentials(credentials_input)
    if input_credentials_test:
        logger.debug("updated credentials with input")
        return credentials_input, False
    elif stored_credentials_test:
        logger.debug("keep good stored credentials")
        return credentials_stored, False

    logger.warning("no credentials available")
    return None, True


@callback(
    Output("dataframe", "data"),
    Output("toast-container", "children"),
    Input("location", "pathname"),
    Input("location", "search"),
    Input("credentials", "data"),
)
def get_hakai_data(path, query, credentials):
    def _make_toast_error(message):
        return dbc.Toast(
            message,
            header="Hakai Download Error",
            dismissable=True,
            icon='danger',
            style={"position": "fixed", "top": 66, "right": 10},
        )
    logger.info("Load hakai data")
    if not credentials or not query:
        logger.warning("No query or credentials available")
        return None, None
    client = Client(credentials=credentials)
    if "limit=" not in query:
        query += "&limit=-1"
    url = f"{client.api_root}/{location_endpoint_mapping[path]}?{query[1:]}"
    logger.debug("run hakai query: %s", url)

    response = client.get(url)
    if response.status_code == 200:
        result = response.json()
        if not result:
            return None, _make_toast_error("No data available")
        logger.debug("result: %s", pd.DataFrame(result).head())
        return response.json(), None
    logger.debug("failed hakai query: %s", response.text)
    response_parsed = json.loads(response.text)
    return None, _make_toast_error(response_parsed['hint'])
