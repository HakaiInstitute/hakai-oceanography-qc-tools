import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, callback, ctx, dcc, html
from loguru import logger

from hakai_qc.nutrients import get_nutrient_statistics
from hakai_qc_app.variables import PRIMARY_VARIABLES, VARIABLES_LABEL

stores = dbc.Col(
    dbc.Spinner(
        [
            dcc.Store(id="dataframe"),
            dcc.Store(id="dataframe-variables"),
            dcc.Store(id="qc-update-data"),
            dcc.Store(id="qc-source-data"),
            dcc.Store(id="main-graph-spinner"),
            dcc.Store(id="auto-qc-nutrient-spinner"),
            dcc.Store(id="figure-menu-label-spinner"),
        ],
        color="light",
        spinner_style={"width": "20px", "height": "20px"},
    ),
    align="center",
    style={"width": "25px", "float": "center"},
)
navbar_menu = dbc.Nav(
    [
        dbc.NavItem(
            dbc.NavLink(
                "Nutrients",
                href="/nutrients",
                className="ms-auto",
                active="partial",
                external_link=True,
            )
        ),
        dbc.NavItem(
            dbc.NavLink("CTD", href="/ctd", active="partial", external_link=True)
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Chlorophyll",
                href="/chlorophyll",
                disabled=True,
                className="me-1",
                active="partial",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(className="bi bi-house-fill me-1", id="welcome-button")
        ),
        dbc.NavItem(
            dbc.NavLink(className="bi bi-filter-circle-fill me-1", id="filter-by")
        ),
        dbc.NavItem(
            dbc.NavLink(
                className="bi bi-search me-1",
                id="qc-button",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                className="bi bi-bar-chart me-1",
                id="stats-button",
            )
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Statistics")),
                dbc.ModalBody("A large modal.", id="stats-modal-body"),
            ],
            id="stats-modal",
            size="large",
        ),
        dbc.NavItem(dbc.NavLink(className="bi me-1", id="log-in")),
    ],
    className="ms-auto",
)

data_filter_interface = dbc.Collapse(
    dbc.Card(
        [
            dbc.CardHeader("Filter data by"),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(id="dataframe-subsets"),
                            dbc.Col(
                                dbc.Input(
                                    id={"type": "dataframe-subset", "subset": "query"},
                                    placeholder="Filter data ...",
                                    type="text",
                                    debounce=True,
                                ),
                                md=4,
                            ),
                        ],
                        align="center",
                        justify="center",
                    ),
                    dbc.Row(
                        [
                            "Filter by time: ",
                            dbc.Col(
                                dcc.DatePickerRange(
                                    id="time-filter-range-picker",
                                    clearable=True,
                                ),
                                width=3,
                            ),
                            dbc.Col(
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            id="filter-time-button-move-down",
                                            className="bi bi-arrow-left me-1",
                                        ),
                                        dbc.Button(
                                            id="filter-time-button-move-up",
                                            className="bi bi-arrow-right me-1",
                                        ),
                                    ]
                                ),
                                width=1,
                            ),
                        ],
                        align="center",
                        justify="center",
                        className="filter-by-time",
                    ),
                ]
            ),
        ]
    ),
    id="data-selection-interface",
    className="data-selection-interface",
    is_open=False,
)


@callback(
    Output("stats-modal", "is_open"),
    Output("stats-modal-body", "children"),
    Input("stats-button", "n_clicks"),
    State("location", "pathname"),
    State("dataframe", "data"),
)
def open_stats_modal(n_clicks, location, data):  # Generate stats
    if n_clicks is None:
        return False, []

    df = pd.DataFrame(data)
    content = None
    if "nutrients" in location:
        stats_items = get_nutrient_statistics(df)
        content = html.Div(
            [
                "pool",
                str(stats_items["pool_standard_deviation"]),
                "distribution",
                dcc.Graph(figure=stats_items["distribution"]),
            ]
        )

    return True, content


@callback(
    Output("data-selection-interface", "is_open"),
    Output("filter-by", "active"),
    Input("filter-by", "n_clicks"),
    State("data-selection-interface", "is_open"),
)
def showfilter_by_section(n_clicks, is_open):
    return 2 * [not is_open] if n_clicks else (False, False)


@callback(
    Output("qc-button", "active"),
    Output("selection-interface", "is_open"),
    Output("location", "hash"),
    Input("qc-button", "n_clicks"),
    State("selection-interface", "is_open"),
    Input("location", "hash"),
)
def show_qc_section(n_clicks, is_open, hash):
    logger.debug(
        "trigger qc section: trigger={}, click={},is_open={},hash={}",
        ctx.triggered_id,
        n_clicks,
        is_open,
        hash,
    )
    if ctx.triggered_id == "location":
        logger.debug("qc section triggerd by location")
        return "#qc" in hash, "#qc" in hash, hash
    logger.debug("qc section triggered by button")
    if n_clicks is None:
        return is_open, is_open, hash
    return (
        not is_open,
        not is_open,
        hash.replace("#qc", "") if is_open else hash + "#qc",
    )


@callback(
    Output("figure-menu", "is_open"),
    Output("figure-menu-button", "active"),
    Input("figure-menu-button", "n_clicks"),
    State("figure-menu", "is_open"),
)
def open_figure_menu(clicked, is_open):
    return (not is_open, not is_open) if clicked else (False, False)


@callback(
    Output("variable", "value"),
    Output("variable", "options"),
    State("variable", "value"),
    Input("dataframe-variables", "data"),
    Input("location", "pathname"),
)
def get_variable_list(value, options, path):
    if not options:
        return None, None
    location_items = path.split("/")
    logger.debug("dataframe-variables={}", options)
    options = [
        {"label": VARIABLES_LABEL.get(option, option), "value": option}
        for option in options.split(",")
        if option in PRIMARY_VARIABLES[location_items[1]]
    ]

    # If value given in url use that
    if len(location_items) > 2:
        value = location_items[2]
        logger.debug("variable value={} from path={}", value, path)
    return value or (options[0]["value"] if options else None), options


@callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(
                            html.Img(
                                src="assets/logo.png",
                                height="40px",
                            )
                        ),
                        dbc.Col(dbc.NavbarBrand("Quality Control"), className="ms-2"),
                        dbc.Col(
                            dcc.Dropdown(
                                id="variable",
                                clearable=False,
                                className="selection-box me-2",
                            )
                        ),
                        stores,
                    ],
                    align="center",
                    className="g-0 align-middle",
                ),
                style={"textDecoration": "none"},
            ),
            dbc.Row(
                [
                    dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
                    dbc.Collapse(
                        navbar_menu,
                        id="navbar-collapse",
                        is_open=False,
                        navbar=True,
                    ),
                ],
                className="flex-grow-1",
            ),
        ],
        className="header-container",
    ),
    color="#B52026",
    dark=True,
)


@callback(
    Output("dataframe-variables", "data"),
    Output("dataframe-subsets", "children"),
    Output("time-filter-range-picker", "min_date_allowed"),
    Output("time-filter-range-picker", "max_date_allowed"),
    Input("dataframe", "data"),
    State("location", "pathname"),
)
def generate_filter_pannel(data, path):
    """Parse downloaded data and generate the different subsets and time
    filters
    """
    if data is None:
        return [], [], None, None

    logger.debug("Load data as dataframe to build filter")
    df = pd.DataFrame(data)
    path = path.split("/")[1]
    if path == "nutrients":
        subset_variables = ["site_id", "line_out_depth"]
        time_variable = "collected"
    elif path == "ctd":
        subset_variables = ["station", "direction_flag"]
        time_variable = "start_dt"
    else:
        raise RuntimeError("Unknown data type to generate filter")

    # Get time interval
    time = pd.to_datetime(df[time_variable])
    time_min = time.min()
    time_max = time.max()

    # Retrieve subsets and generate dropdowns
    logger.debug("Retrieve subsets variables")
    subsets = {var: df[var].unique() for var in subset_variables}
    subset_interface = [
        dbc.Row(
            [
                dbc.Col(
                    dcc.Dropdown(
                        id={"type": "dataframe-subset", "subset": key},
                        options=options,
                        multi=True,
                        className="selection-box",
                        placeholder=key,
                    ),
                )
                for key, options in subsets.items()
            ]
        ),
    ]
    return (
        ",".join(df.columns),
        subset_interface,
        time_min.to_pydatetime(),
        time_max.to_pydatetime(),
    )


@callback(
    Output("time-filter-range-picker", "start_date"),
    Output("time-filter-range-picker", "end_date"),
    State("time-filter-range-picker", "start_date"),
    State("time-filter-range-picker", "end_date"),
    Input("filter-time-button-move-down", "n_clicks"),
    Input("filter-time-button-move-up", "n_clicks"),
)
def update_date_range_slider(picker_date_min, picker_date_max, down, up):
    if picker_date_min is None or picker_date_max is None:
        return None, None
    start = pd.to_datetime(picker_date_min)
    end = pd.to_datetime(picker_date_max)
    time_interval = (end - start) + pd.Timedelta(1, unit="days")
    if ctx.triggered_id == "filter-time-button-move-down":
        logger.debug("Move time filter slider down")
        time_interval = -time_interval
    elif ctx.triggered_id == "filter-time-button-move-up":
        logger.debug("Move time filter slider up")
    start += time_interval
    end += time_interval
    logger.debug(
        "Move time filter slider: [{},{}] by {} = [{},{}]",
        picker_date_min,
        picker_date_max,
        time_interval,
        start,
        end,
    )
    return start, end
