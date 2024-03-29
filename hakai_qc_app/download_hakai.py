import base64
import binascii
import json
import re
from datetime import datetime, timezone
from urllib.parse import unquote

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, ctx, dcc, html
from hakai_api import Client
from loguru import logger

from hakai_qc import ctd, nutrients
from hakai_qc_app.__version__ import __version__
from hakai_qc_app.variables import pages


def parse_hakai_token(token):
    info = dict(item.split("=", 1) for item in token.split("&"))
    base64_bytes = info["access_token"].encode("ascii")
    for padding_ignore in range(1, 12):
        try:
            message_bytes = base64.b64decode(base64_bytes[:-padding_ignore])
            if not message_bytes:
                logger.debug("read token[:-{}]=''")
                continue
            break
        except binascii.Error or RuntimeError:
            logger.debug("failed to read token[:-{}]", padding_ignore)

    message = message_bytes.decode("ascii", "ignore")
    # remove trailing characters after '"}'
    message = message.rsplit('"}',1)[0] + '"}'
    logger.debug("Decoded token={}", message)
    if message is None:
        logger.error("failed to decode token")
        return None
    logger.info("Token decoded='{}'", message)
    return json.loads('{"id":' + message.split('{"id":', 1)[1].rsplit("}", 1)[0] + "}")


def _test_hakai_api_credentials(token):
    """Test hakai api credential token"""
    if token is None:
        return None, "credentials unavailable"
    try:
        credentials = parse_hakai_token(token)
        logger.debug("Parsed token={}", credentials)
        if datetime.now(timezone.utc).timestamp() > credentials["exp"]:
            return None, "Credentials are expired"
        return credentials, "Valid Credentials"
    except Exception as exception:
        logger.exception("Failed to parse credentials")
        return None, f"Failed to parse credentials: {exception}"


hakai_api_credentials_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Hakai Credentials"), close_button=True),
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
                dbc.FormFloating(
                    [
                        dbc.Input(
                            id="user-initials",
                            type="text",
                            min=2,
                            max=10,
                            pattern="[A-Z]+",
                            persistence=True,
                            persistence_type="local",
                            size="small",
                        ),
                        dbc.Label("User Initials: "),
                    ],
                ),
                html.Br(),
                html.Sub(
                    f"v{__version__}: {datetime.utcnow().isoformat()[:19]}",
                    id="deployment-info",
                    className="deployment-info",
                ),
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
    Output("log-in", "children"),
    Output("user-initials", "value"),
    Output("select-work-area", "options"),
    Output("credentials-spinners", "children"),
    Input("credentials-input", "value"),
    State("user-initials", "value"),
)
def test_credentials(credentials, user_initials):
    logger.debug("read credentials token={}", credentials)
    parsed_credentials, message = _test_hakai_api_credentials(credentials)
    logger.debug("parsed credentials = {}", parsed_credentials)
    is_valid = bool(parsed_credentials)
    logger.info("Hakai Token Credential is: {}", is_valid)
    if is_valid and user_initials is None:
        # If no initials is already filled
        # use the credential name to generate initials
        user_initials = "".join(
            [letter for letter in parsed_credentials["name"] if letter.isupper()]
        )
    return (
        is_valid,
        not is_valid,
        html.Img(
            src=parsed_credentials["picture"], height="30px", className="log-in-icon"
        )
        if is_valid
        else html.I(className="bi bi-person-circle me-1"),
        user_initials,
        parsed_credentials["workareas"] if is_valid else None,
        dbc.Alert(message, color="success" if is_valid else "danger"),
    )


@callback(
    Output("dataframe", "data"),
    Output("toast-container", "children"),
    Output("qc-source-data", "data"),
    State("location", "pathname"),
    State("location", "search"),
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
            logger.debug("Hakai Error= {} : {}", response.status_code, response.text)
            return None, _make_toast_error(f"Failed to download data: {response}")

        result = response.json()
        logger.info(
            "Hakai {} records downloaded from {}", len(result), url.split("&fields")[0]
        )
        return (
            (result, None) if result else (None, _make_toast_error("No Data Retrieved"))
        )

    logger.debug("load data triggered by {}", ctx.triggered_id)

    # if viewing home page do not downloading anything
    path = path.split("/")[1]
    if path == ["/"]:
        logger.debug("do not load anything from front page path='/")
        return None, None, None
    elif path not in pages:
        logger.warning("Unknown data type")
        return None, None, None
    elif not query:
        logger.debug("no query given")
        return None, None, None

    logger.debug("Load from path={}", path)
    endpoints = pages[path]
    main_endpoint = endpoints[0]
    client = Client(credentials=credentials)
    query = unquote(query)
    url = f"{client.api_root}/{main_endpoint['endpoint']}?{query[1:]}"
    logger.debug("run hakai query: {}", url)
    result, toast_error = _get_data(url, main_endpoint.get("fields"))
    if toast_error:
        return (
            None,
            toast_error or _make_toast_error("No data available"),
            [],
        )
    logger.debug("data downloaded")

    # Generate derived variables
    logger.debug("Generate derived variables")
    df = pd.DataFrame(result)
    if path == "ctd":
        df = ctd.get_derive_variables(df)
    elif path == "nutrients":
        df = nutrients.get_derived_variables(df)
    result = df.to_dict(orient="records")

    # Load auxiliary data
    if path == "ctd":
        flag_filters = re.findall("(station|start_dt)(=|<|>|>=|<=)([^&]*)", url)
        flag_filters = [
            "".join(item).replace("station", "site_id").replace("start_dt", "collected")
            for item in flag_filters
        ]
        url_flags = (
            f"{client.api_root}/"
            f"{endpoints[1]['endpoint']}?"
            f"{'&'.join(flag_filters)}"
        )
        logger.debug("Retrieve CTD flags: {}", url_flags)
        result_flags, toast_error = _get_data(url_flags, endpoints[1].get("fields"))
        if toast_error:
            logger.debug("failed to get ctd flag data")
            return (
                None,
                toast_error or _make_toast_error("No data available"),
                None,
            )
        logger.debug("CTD flag downloaded")
    else:
        logger.debug("no auxiliary data retrieved")
        result_flags = result

    return result, None, result_flags
