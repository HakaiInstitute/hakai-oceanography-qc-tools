import logging
from datetime import date

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, ctx, dcc, html
from hakai_api import Client

from utils import load_config

logger = logging.getLogger(__name__)
config = load_config()

welcome_title = dbc.Row(
    [
        dbc.Col("Hakai Data Dashboard", width="auto"),
        dbc.Col(
            dbc.Spinner(
                [
                    html.Div(id="load-work-areas"),
                    html.Div(id="load-sites"),
                ],
                color="light",
                spinner_style={"width": "20px", "height": "20px"},
            ),
            align="center",
            style={"width": "35px", "float": "center"},
        ),
    ],
    className="g-0 align-middle",
)
welcome_section = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle(welcome_title), className="welcome-header"),
        dbc.ModalBody(
            [
                dcc.Markdown(
                    [
                        "Welcome to the hakai dashboard where you can visualize and QC Hakai data.\n ",
                        "Please first select which data you want to look at, the station and time interval:",
                    ]
                ),
                dbc.Stack(
                    [
                        dbc.Select(
                            options=[
                                {"label": item.title(), "value": item}
                                for item in config["pages"].keys()
                            ],
                            id="select-data-type",
                            placeholder="Data Type",
                        ),
                        dbc.Select(id="select-work-area", placeholder="Work Area"),
                        dbc.Select(id="select-station", placeholder="Station"),
                        dcc.DatePickerRange(
                            id="select-date-range",
                            min_date_allowed=date(2012, 1, 1),
                            max_date_allowed=date.today(),
                            start_date=date(date.today().year - 1, 1, 1),
                            end_date=date.today(),
                        ),
                        html.Br(),
                        html.Div(id="run-search-selection"),
                    ],
                    gap=2,
                    className="welcome-selection-inputs",
                ),
            ]
        ),
    ],
    size="lg",
    id="welcome-section",
    backdrop="static",
    centered=True,
)


@callback(
    Output("select-station", "options"),
    Output("load-sites", "children"),
    Input("select-data-type", "value"),
    State("credentials-input", "value"),
    Input("select-work-area", "value"),
)
def get_station_list(data_type, credentials, work_area):
    if data_type is None:
        return None, None

    client = Client(credentials=credentials)
    logger.debug("Get station list for data_type=%s", data_type)
    if data_type == "ctd":
        site_label = "station"
    else:
        site_label = "site_id"
    work_area_filter = f"work_area={work_area}&" if work_area else ""
    response = client.get(
        f"{client.api_root}/{config['pages'][data_type][0]['endpoint']}?{work_area_filter}fields={site_label}&sort={site_label}&limit=-1&distinct"
    )
    logger.debug("resulting response=%s", response.text)
    return [item[site_label] for item in response.json()], None


# @callback(
#     Output("hide-all-figure-area", "is_open"),
#     Output("welcome-section", "is_open"),
#     Input({"type": "graph", "page": "main"}, "figure"),
# )
# def show_all_figure(figure):
#     return bool(figure), not bool(figure)


@callback(
    Output("welcome-section", "is_open"),
    Input("location", "pathname"),
    Input("location", "search"),
    Input("credentials-input", "valid"),
)
def show_welcome_page(path, search, valid_credentials):
    if not valid_credentials:
        return False
    path = path.split("/")[1]
    return path not in config["pages"] or len(search) < 10


@callback(
    Output("select-work-area", "options"),
    Output("load-work-areas", "children"),
    Input("select-data-type", "value"),
    State("credentials-input", "value"),
)
def get_work_area_list(data_type, credentials):
    if data_type is None:
        return None, None

    client = Client(credentials=credentials)
    logger.debug("Get work_area list for data_type=%s", data_type)
    response = client.get(
        f"{client.api_root}/{config['pages'][data_type][0]['endpoint']}?fields=work_area&sort=work_area&limit=-1&distinct"
    )
    logger.debug("resulting response=%s", response.text)
    return [item["work_area"] for item in response.json()], None


@callback(
    Output("run-search-selection", "children"),
    Input("select-data-type", "value"),
    Input("select-work-area", "value"),
    Input("select-station", "value"),
    Input("select-date-range", "start_date"),
    Input("select-date-range", "end_date"),
    Input("location", "search"),
)
def get_hakai_search_url(
    data_type,
    work_area,
    station,
    start_date,
    end_date,
    search,
):
    if data_type is None or work_area is None or station is None:
        return []

    time_label = "start_dt" if data_type == "ctd" else "collected"
    site_label = "station" if data_type == "ctd" else "site_id"
    search = "&".join(
        [
            f"work_area={work_area}",
            f"{site_label}={station}",
            f"{time_label}>{start_date}" if start_date else "",
            f"{time_label}<{end_date}" if end_date else "",
        ]
    )
    link = f"/{data_type}?{search}"
    return [
        "Click the following link to review data: ",
        html.Br(),
        dcc.Link(title="Selected query", href=link, refresh=True),
    ]