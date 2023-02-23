import logging
import re
import webbrowser
from time import time
import json

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, dcc, html, ctx
from hakai_api import Client

from utils.tools import load_config

logger = logging.getLogger(__name__)
config = load_config()


def parse_hakai_token(token):
    if token is None:
        return {"expires_at": 0}
    parsed_token = dict(item.split("=") for item in token.split("&"))
    parsed_token["expires_at"] = int(parsed_token["expires_at"])
    return parsed_token


def _test_hakai_api_credentials(creds):
    if creds is None:
        return False, None
    try:
        client = Client(credentials=creds)
        response = client.get(f"{client.api_root}/ctd/views/file/cast?limit=10")
        if response.status_code != 200:
            response.raise_for_status()
        # Should return a 404 error
        return True, (False, dbc.Alert("Valid Credentials", color="success"))
    except Exception as e:
        return (
            False,
            dbc.Alert(
                [html.H5("Credentials failed"), html.Hr(), html.P(repr(e))],
                color="danger",
            ),
        )


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
                dbc.Spinner(html.Div(id="credentials-spinners")),
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
    Input("credentials", "data"),
    Input("credentials-input", "valid"),
    State("credentials-input", "value"),
    Input("log-in", "n_clicks"),
)
def review_stored_credentials(
    credentials_stored, valid_credentials_input, credential_input, log_in_clicks
):
    triggered_id = ctx.triggered_id
    if triggered_id == "log-in":
        logger.debug("clicked on log-in")
        return credentials_stored, True
    elif triggered_id == "credentials-input":
        if valid_credentials_input:
            logger.debug("save valid credentials input")
            return credential_input, False
        else:
            logger.debug("bad credentials input")
            return None, True

    stored_credentials_test, _ = _test_hakai_api_credentials(credentials_stored)
    if stored_credentials_test:
        logger.debug("keep good stored credentials")
        return credentials_stored, False
    logger.warning("no credentials available")
    return None, True


@callback(
    Output("credentials-input", "valid"),
    Output("credentials-input", "invalid"),
    Output("credentials-spinners", "children"),
    Input("credentials-input", "value"),
)
def review_input_credentials(credentials):
    is_valid, error_toast = _test_hakai_api_credentials(credentials)
    return is_valid, not is_valid, error_toast


@callback(
    Output("dataframe", "data"),
    Output("variable", "options"),
    Output("line-out-depth-selector", "options"),
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
            icon="danger",
            style={"position": "fixed", "top": 66, "right": 10},
        )

    logger.info("Load hakai data")
    if not credentials or not query:
        logger.info("No query or credentials available")
        return None, None, None, None
    client = Client(credentials=credentials)
    if "limit=" not in query:
        query += "&limit=-1"
    url = f"{client.api_root}/{location_endpoint_mapping[path]}?{query[1:]}"
    logger.debug("run hakai query: %s", url)

    response = client.get(url)
    if response.status_code != 200:
        logger.debug("failed hakai query: %s", response.text)
        response_parsed = json.loads(response.text)
        return None, None, None, _make_toast_error(response_parsed["hint"])
    # No data  available
    result = response.json()
    if not result:
        return None, None, None, _make_toast_error("No data available")
    logger.debug("result: %s", pd.DataFrame(result).head())

    # Review data to extract needed data
    df = pd.DataFrame(result)
    if "line_out_depth" in df:
        line_out_depths = df["line_out_depth"].drop_duplicates().sort_values().to_list()
    else:
        line_out_depths = None

    variables = [
        {"label": config["VARIABLES_LABEL"].get(var, var), "value": var}
        for var in df.columns
        if var in config["PRIMARY_VARIABLES"]
    ]
    logger.debug("variables available %s", variables)
    logger.debug("line_out_depths available %s", line_out_depths)
    return result, variables, line_out_depths, None
