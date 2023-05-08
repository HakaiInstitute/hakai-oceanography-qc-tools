import logging

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html, ctx
from utils import load_config

config = load_config()
logger = logging.getLogger(__name__)

stores = dbc.Col(
    dbc.Spinner(
        [
            dcc.Store(id="dataframe"),
            dcc.Store(id="dataframe-variables"),
            dcc.Store(id="selected-data"),
            dcc.Store(id={"id": "selected-data", "source": "auto-qc"}),
            dcc.Store(id={"id": "selected-data", "source": "figure"}),
            dcc.Store(id={"id": "selected-data", "source": "flags"}),
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
                "Nutrients", href="/nutrients", className="ms-auto", active="partial"
            )
        ),
        dbc.NavItem(dbc.NavLink("CTD", href="/ctd", active="partial")),
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
            dbc.NavLink(className="bi bi-filter-circle-fill me-1", id="filter-by")
        ),
        dbc.NavItem(
            dbc.NavLink(
                className="bi bi-search me-1",
                id="qc-button",
            )
        ),
        dbc.NavItem(dbc.NavLink(className="bi bi-person-circle me-1", id="log-in")),
    ],
    className="ms-auto",
)

data_filter_interface = dbc.Collapse(
    dbc.Card(
        [
            dbc.CardHeader("Filter data by"),
            dbc.CardBody(
                [
                    dbc.Row(id="dataframe-subsets", align="center", justify="center"),
                    html.Div(
                        dbc.Button(
                            "Apply filter",
                            id="apply-subset-filetr",
                            className="d-grid gap-2 col-6 mx-auto update-figure-button",
                        )
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
    Input("selection-interface", "is_open"),
    State("location", "hash"),
)
def show_qc_section(n_clicks, is_open, hash):
    logger.debug(
        "trigger qc section: trigger=%s, click=%s,is_open=%s,hash=%s",
        ctx.triggered_id,
        n_clicks,
        is_open,
        hash,
    )
    if "#qc" in hash and ctx.triggered_id == "location":
        return True, True, hash
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
    State("location", "pathname"),
)
def get_variable_list(value, options, path):
    if options is None:
        return None, None
    location_items = path.split("/")
    logger.debug("dataframe-variables=%s", options)
    options = [
        {"label": config["VARIABLES_LABEL"].get(option, option), "value": option}
        for option in options.split(",")
        if option in config["PRIMARY_VARIABLES"][location_items[1]]
    ]

    # If value given in url use that
    if len(location_items) > 2:
        value = location_items[2]
        logger.debug("variable value=%s from path=%s", value, path)
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
                        dbc.Col(html.Img(src="assets/logo.png", height="40px")),
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
        ]
    ),
    color=config["NAVBAR_COLOR"],
    dark=config["NAVBAR_DARK"],
)
