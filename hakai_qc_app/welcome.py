from datetime import date

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html
from hakai_api import Client
from loguru import logger

from hakai_qc_app.utils import load_config

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
        dbc.ModalHeader(
            dbc.ModalTitle(welcome_title),
            className="welcome-header",
            close_button=False,
        ),
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
                                {
                                    "label": config["VARIABLES_LABEL"].get(
                                        item, item.title()
                                    ),
                                    "value": item,
                                }
                                for item in config["pages"].keys()
                            ],
                            id="select-data-type",
                            placeholder="Data Type",
                            persistence=True,
                        ),
                        dbc.Select(
                            id="select-work-area",
                            placeholder="Work Area",
                            persistence=True,
                        ),
                        dbc.Select(
                            id="select-survey", placeholder="Survey", persistence=True
                        ),
                        dbc.Select(
                            id="select-station", placeholder="Station", persistence=True
                        ),
                        dcc.DatePickerRange(
                            id="select-date-range",
                            min_date_allowed=date(2012, 1, 1),
                            max_date_allowed=date.today(),
                            start_date=date(date.today().year - 1, 1, 1),
                            end_date=date.today(),
                            persistence=True,
                        ),
                        dbc.FormFloating(
                            [
                                dbc.Input(type="text", id="select-extra"),
                                dbc.Label("Extra filter"),
                            ]
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


def list_to_select_dict(options: list):
    return [{"label": option, "value": option} for option in options]


@callback(
    Output("select-station", "options"),
    Output("load-sites", "children"),
    Input("select-data-type", "value"),
    State("credentials-input", "value"),
    Input("select-work-area", "value"),
    Input("select-survey", "value"),
    State("select-date-range", "start_date"),
    State("select-date-range", "end_date"),
)
def get_station_list(data_type, credentials, work_area, survey, start_date, end_date):
    if data_type is None:
        return None, None

    client = Client(credentials=credentials)
    logger.debug("Get station list for data_type={}", data_type)

    # Map variables to data_type
    if data_type == "ctd":
        site_label = "station"
        time_variable = "start_dt"
        survey_variable = "cruise"
    else:
        site_label = "site_id"
        time_variable = "collected"
        survey_variable = "survey"

    work_area_filter = f"work_area={work_area}&" if work_area else ""
    survey_filter = f"{survey_variable}={survey}&" if survey else ""
    response = client.get(
        f"{client.api_root}/{config['pages'][data_type][0]['endpoint']}?"
        f"{work_area_filter}{survey_filter}"
        f"fields={site_label}&sort={site_label}&limit=-1&distinct"
        f"&{time_variable}>={start_date}"
        f"&{time_variable}<={end_date}"
    )
    stations = [item[site_label] for item in response.json()]
    logger.debug("station list response={}", stations)
    return list_to_select_dict(stations), None


@callback(
    Output("select-survey", "options"),
    Input("select-data-type", "value"),
    State("credentials-input", "value"),
    Input("select-work-area", "value"),
    State("select-date-range", "start_date"),
    State("select-date-range", "end_date"),
)
def get_survey_list(data_type, credentials, work_area, start_date, end_date):
    if data_type is None:
        return None

    client = Client(credentials=credentials)
    logger.debug("Get survey list for data_type={}", data_type)
    time_variable = "start_dt" if data_type == "ctd" else "collected"
    survey_variable = "cruise" if data_type == "ctd" else "survey"
    work_area_filter = f"work_area={work_area}&" if work_area else ""
    response = client.get(
        f"{client.api_root}/{config['pages'][data_type][0]['endpoint']}?"
        f"{work_area_filter}"
        f"fields={survey_variable}&sort={survey_variable}&limit=-1&distinct"
        f"&{time_variable}>={start_date}"
        f"&{time_variable}<={end_date}"
    )
    surveys = [None] + [item[survey_variable] for item in response.json()]
    logger.debug("survey response={}", surveys)
    return list_to_select_dict(surveys)


@callback(
    Output("select-data-type", "value"),
    Input("location", "pathname"),
    Input("welcome-section", "is_open"),
)
def get_datatype_from_pathname(pathname, welcome_is_open):
    if not welcome_is_open or pathname in ("/", None):
        return None
    data_type = [item for item in config["pages"] if item in pathname]
    logger.info("Data type given by path: {}", data_type)
    return data_type[0] if data_type else None


@callback(
    Output("welcome-section", "is_open"),
    Input("location", "pathname"),
    Input("location", "search"),
    Input("credentials-input", "valid"),
)
def show_welcome_page(path, search, valid_credentials):
    if not valid_credentials:
        return False
    data_type = path.split("/")[1]
    logger.debug("show welcome for data_type={} in path={}", data_type, path)
    no_search = len(search) < 10
    unknown_datatype = data_type not in config["pages"]
    logger.debug("no_search={} or unknown_datatype= {}", no_search, unknown_datatype)
    return unknown_datatype or no_search


@callback(Output("select-extra", "value"), Input("select-data-type", "value"))
def apply_default_extra_filters(data_type):
    return "direction_flag=d" if data_type == "ctd" else None


@callback(
    Output("run-search-selection", "children"),
    Input("select-data-type", "value"),
    Input("select-work-area", "value"),
    Input("select-survey", "value"),
    Input("select-station", "value"),
    Input("select-date-range", "start_date"),
    Input("select-date-range", "end_date"),
    Input("select-extra", "value"),
    Input("location", "search"),
)
def get_hakai_search_url(
    data_type,
    work_area,
    survey,
    station,
    start_date,
    end_date,
    extra,
    search,
):
    if data_type is None or station is None:
        return []

    time_label = "start_dt" if data_type == "ctd" else "collected"
    site_label = "station" if data_type == "ctd" else "site_id"
    survey_label = "cruise" if data_type == "ctd" else "survey"
    search = "&".join(
        [
            item
            for item in [
                f"work_area={work_area}" if work_area else None,
                f"{survey_label}={survey}" if survey else None,
                f"{site_label}={station}",
                f"{time_label}>{start_date}" if start_date else "",
                f"{time_label}<{end_date}" if end_date else "",
                extra,
            ]
            if item
        ]
    )
    link = f"/{data_type}?{search}"
    return [
        "Click the following link to review data: ",
        html.Br(),
        dcc.Link(title="Selected query", href=link, refresh=True),
    ]
