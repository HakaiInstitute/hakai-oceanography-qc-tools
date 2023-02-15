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


# endpoints = [
#     {"label": "nutrients", "value": "eims/views/output/nutrients"},
#     {"label": "chlorophyll", "value": "eims/views/output/chlorophyll"},
# ]

# download_hakai_eims = [
#     # dbc.Label("EIMS Endpoint"),
#     dbc.Col(
#         dcc.Dropdown(
#             id="hakai-endpoint",
#             options=endpoints,
#             value="nutrients",
#             placeholder="Endpoint",
#             className="hakai-endpoint",
#             clearable=False,
#             persistence=True,
#             persistence_type="local",
#         ),
#         className="me-3",
#     ),
#     # dbc.Label("Work Area"),
#     dbc.Col(
#         dcc.Dropdown(
#             id="hakai-organization",
#             value="HAKAI",
#             placeholder="Organization",
#             className="organization",
#         ),
#         className="me-3",
#     ),
#     dbc.Col(
#         dcc.Dropdown(
#             id="hakai-work-area",
#             placeholder="Work Area",
#             className="work-area",
#         ),
#         className="me-3",
#     ),
#     # dbc.Label("Station"),
#     dbc.Col(
#         dcc.Dropdown(
#             id="hakai-station",
#             placeholder="Station",
#             className="station",
#         ),
#         className="me-3",
#     ),
#     # dbc.Label("Time Range"),
#     dbc.Col(
#         dcc.DatePickerRange(
#             start_date_placeholder_text="From",
#             end_date_placeholder_text="To",
#             clearable=True,
#             display_format="YYYY-MM-DD",
#             id="hakai-query-date-range",
#             className="hakai-query-date-range",
#         )
#     ),
#     dbc.Col(
#         dbc.Button(
#             "Apply",
#             id="update-hakai-query",
#             outline=True,
#             color="primary",
#         )
#     ),
# ]


# @callback(
#     Output("hakai-organization", "options"),
#     State("credentials", "data"),
#     Input("hakai-endpoint", "value"),
# )
# def get_work_area(credentials, endpoint):
#     if not credentials or not endpoint:
#         return []
#     client = Client(credentials=credentials)
#     response = client.get(
#         f"{client.api_root}/{endpoint}?fields=organization&distinct&limit=-1"
#     )
#     if response.status_code != 200:
#         logger.error(response.text)
#     return [item["organization"] for item in response.json()]


# @callback(
#     Output("hakai-work-area", "options"),
#     State("credentials", "data"),
#     State("hakai-endpoint", "value"),
#     Input("hakai-organization", "value"),
# )
# def get_work_area(credentials, endpoint, organization):
#     if not credentials or not endpoint:
#         return []
#     client = Client(credentials=credentials)
#     response = client.get(
#         f"{client.api_root}/{endpoint}?fields=work_area&organization={organization}&distinct&limit=-1"
#     )
#     if response.status_code != 200:
#         logger.error(response.text)
#     return [item["work_area"] for item in response.json()]


# @callback(
#     Output("hakai-station", "options"),
#     State("credentials", "data"),
#     State("hakai-endpoint", "value"),
#     State("hakai-organization", "value"),
#     Input("hakai-work-area", "value"),
# )
# def get_work_area(credentials, endpoint, organization, work_area):
#     if not credentials or not endpoint or not organization or not work_area:
#         return []
#     client = Client(credentials=credentials)
#     response = client.get(
#         f"{client.api_root}/{endpoint}?fields=site_id&organization={organization}&work_area={work_area}&distinct&limit=-1"
#     )
#     logger.debug("site_ids:%s", response.json())
#     return [item["site_id"] for item in response.json()]


# @callback(
#     Output("location", "search"),
#     Input("update-hakai-query", "n_clicks"),
#     State("hakai-endpoint", "value"),
#     State("hakai-organization", "value"),
#     State("hakai-work-area", "value"),
#     State("hakai-station", "value"),
#     State("credentials", "data"),
# )
# def update_query(nclicks, endpoint, organization, work_area, station, credentials):
#     client = Client(credentials=credentials)
#     url = f"{endpoint}?"
#     filter_url = ["limit=-1"]
#     if organization:
#         filter_url += [f"organization={organization}"]
#     if work_area:
#         filter_url += [f"work_area={work_area}"]
#     if station:
#         filter_url += [f"station={station}"]
#     url += "&".join(filter_url)
#     return url
