import json
import logging
import re
import webbrowser
from datetime import datetime
from time import mktime, time
from urllib.parse import unquote

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, ctx, dcc, html
from hakai_api import Client
from requests.exceptions import HTTPError

from utils import load_config

logger = logging.getLogger(__name__)
config = load_config()


def parse_hakai_token(token):
    return (
        None if token is None else dict(map(lambda x: x.split("="), token.split("&")))
    )


hakai_token_keys = {"token_type", "access_token", "expires_at"}


def _test_hakai_api_credentials(token):
    """Test hakai api credential token"""
    if token is None:
        return False, "credentials unavailable"
    try:
        credentials = parse_hakai_token(token)
        now = int(
            mktime(datetime.now().timetuple()) + datetime.now().microsecond / 1000000.0
        )
        if now > int(credentials["expires_at"]):
            return False, "Credentials are expired"
        elif set(credentials.keys()) != hakai_token_keys:
            return (
                False,
                f"Credentials is missing the key: {set(credentials.keys()) - hakai_token_keys}",
            )

        return True, "Valid Credentials"
    except Exception as exception:
        return False, f"Failed to parse credentials: {exception}"


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


def fill_hakai_flag_variables(df):
    """Replace hakai flag variables empty values by (*_flag: "NA", *_flag_level_1:9)"""
    fill_hakai_flags = {
        col: "NA"
        for col in df.columns
        if col not in ("direction_flag") and re.match(".*_flag$", col)
    }
    fill_flags_level_1 = {
        col: 9 for col in df.columns if re.match(".*_flag_level_1$", col)
    }
    logger.debug('Fill empty flag values: (*_flag: "NA", *_flag_level_1:9)')
    return df.fillna({**fill_hakai_flags, **fill_flags_level_1})


@callback(
    Output("credentials-modal", "is_open"),
    Input("credentials-input", "valid"),
    Input("log-in", "n_clicks"),
)
def review_stored_credentials(valid_credentials_input, log_in_clicks):
    triggered_id = ctx.triggered_id
    if triggered_id == "log-in":
        logger.debug("clicked on log-in")
        return True
    return not valid_credentials_input


@callback(
    Output("credentials-input", "valid"),
    Output("credentials-input", "invalid"),
    Output("credentials-spinners", "children"),
    Input("credentials-input", "value"),
)
def test_credentials(credentials):
    is_valid, message = _test_hakai_api_credentials(credentials)
    return (
        is_valid,
        not is_valid,
        dbc.Alert(message, color="success" if is_valid else "danger"),
    )


@callback(
    Output("dataframe", "data"),
    Output("dataframe-variables", "data"),
    Output("dataframe-subsets", "children"),
    Output("toast-container", "children"),
    Output({"id": "selected-data", "source": "flags"}, "data"),
    Input("location", "pathname"),
    Input("location", "search"),
    Input("credentials-input", "value"),
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
        try:
            response = client.get(url, timeout=120)
        except Exception as err:
            return None, _make_toast_error(f"Failed to retrieve hakai data:\n{err}")
        if response.status_code == 500:
            parsed_response = json.loads(response.text)
            return None, _make_toast_error(
                f"Failed data query: {parsed_response.get('hint') or response.text}"
            )
        elif response.status_code != 200:
            logger.debug("Hakai Error= %s : %s", response.status_code, response.text)
            return None, _make_toast_error(f"Failed to download data: {response}")

        result = response.json()
        return (
            (result, None) if result else (None, _make_toast_error("No Data Retrieved"))
        )

    # if viewing home page do not downloading anything
    path = path.split("/")[1]
    if path == ["/"]:
        logger.debug("do not load anything from front page path='/")
        return None, None, None, None, None
    elif path not in config["pages"]:
        logger.warning("Unknown data type")
        return None, None, None, None, None
    elif not query:
        logger.debug("no query given")
        return None, None, None, None, None

    logger.debug("Load from path=%s", path)
    endpoints = config["pages"][path]
    main_endpoint = endpoints[0]
    client = Client(credentials=credentials)
    query = unquote(query)
    url = f"{config.get('HAKAI_DEFAULT_API_SERVER_ROOT') or client.api_root}/{main_endpoint['endpoint']}?{query[1:]}"
    logger.debug("run hakai query: %s", url)
    result, toast_error = _get_data(url, main_endpoint.get("fields"))
    if toast_error:
        return (
            None,
            None,
            None,
            toast_error or _make_toast_error("No data available"),
            [],
        )
    logger.debug("data downloaded")
    # Load auxiliary data
    if path == "ctd":
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
        result_flags = result

    # Extract subsets
    df = pd.DataFrame(result)
    if path == "nutrients":
        subset_variables = ["site_id", "line_out_depth"]
    elif path == "ctd":
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
