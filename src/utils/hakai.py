import json
import logging
import re
import webbrowser
from time import time
from urllib.parse import unquote

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, ctx, dcc, html
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
    is_open=False,
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
    elif triggered_id == "credentials-input" or valid_credentials_input:
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
    Output("dataframe-variables", "data"),
    Output("dataframe-subsets", "children"),
    Output("toast-container", "children"),
    Output({"id": "selected-data", "source": "flags"}, "data"),
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

    def _get_data(url, fields=None):
        url += "&limit=-1" if "limit" not in url else ""
        url += "&fields=" + ",".join(fields) if fields else ""
        response = client.get(url)
        if response.status_code != 200:
            logger.debug("failed hakai query: %s", response.text)
            response_parsed = json.loads(response.text)
            return None, _make_toast_error(response_parsed["hint"])
        result = response.json()
        return (
            (result, None) if result else (None, _make_toast_error("No Data Retrieved"))
        )

    # if viewing home page do not downloading anything
    if path == "/":
        logger.debug("do not load anything from front page path='/")
        return None, None, None, None, None

    endpoints = config["pages"][path]
    main_endpoint = endpoints[0]
    client = Client(credentials=credentials)
    query = unquote(query)
    url = f"{client.api_root}/{main_endpoint['endpoint']}?{query[1:]}"
    logger.debug("run hakai query: %s", url)
    result, toast_error = _get_data(url, main_endpoint.get("fields"))
    if toast_error:
        return (
            None,
            None,
            None,
            toast_error or _make_toast_error("No data available"),
            None,
        )
    logger.debug("data downloaded")
    # Load auxiliary data
    if path == "/ctd":
        flag_filters = re.findall("(station|start_dt)(=|<|>|>=|<=)([^&]*)", url)
        url_flags = f"{client.api_root}/{endpoints[1]['endpoint']}?{'&'.join([''.join(item).replace('station','site_id').replace('start_dt','collected') for item in flag_filters])}"
        logger.debug("Retrieve CTD flags: %s", url_flags)
        result_flags, toast_error = _get_data(url_flags, endpoints[1].get("fields"))
        if toast_error:
            logger.debug("failed to get ctd flag data")
            return (
                None,
                None,
                None,
                toast_error or _make_toast_error("No data available"),
                None,
            )
        logger.debug("CTD flag downloaded")
    else:
        logger.debug("no auxiliary data retrieved")
        result_flags = None

    # Extract subsets
    df = pd.DataFrame(result)
    if path == "/nutrients":
        subset_variables = ["site_id", "line_out_depth"]
    elif path == "/ctd":
        subset_variables = ["station", "direction_flag"]
    else:
        subset_variables = {}

    subsets = {var: df[var].unique() for var in subset_variables}
    subset_selection = [
        dbc.Col(
            dcc.Dropdown(
                id={"type": "dataframe-subset", "subset": key},
                options=options,
                multi=True,
                className="selection-box",
                placeholder=key,
            ),
            md=4,
        )
        for key, options in subsets.items()
    ] + [
        dbc.Col(
            dbc.Input(
                id={"type": "dataframe-subset", "subset": "query"},
                placeholder="Filter data ...",
                type="text",
                debounce=True,
            ),
            md=4,
        )
    ]

    logger.debug("variables available %s", df.columns)
    logger.debug("subsets available %s", subset_variables)
    return result, ",".join(df.columns), subset_selection, None, result_flags
