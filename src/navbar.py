import logging

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html


logger = logging.getLogger(__name__)

stores = dbc.Col(
    dbc.Spinner(
        [
            dcc.Store(id="dataframe"),
            dcc.Store(id="selected-data"),
            dcc.Store(id={"id": "selected-data", "source": "auto-qc"}),
            dcc.Store(id={"id": "selected-data", "source": "figure"}),
            dcc.Store(id={"id": "selected-data", "source": "flags"}),
            dcc.Store(id="main-graph-spinner"),
            dcc.Store(id="auto-qc-nutrient-spinner"),
        ],
        color="light",
        spinner_style={"width": "20px", "height": "20px"},
    ),
    align="center",
    style={"width": "25px", "float": "center"},
)
navbar_menu = dbc.Nav(
    [
        dbc.NavItem(dbc.NavLink("Nutrients", href="/nutrients", className="ms-auto")),
        dbc.NavItem(dbc.NavLink("CTD", href="/ctd")),
        dbc.NavItem(
            dbc.NavLink(
                "Chlorophyll", href="/chlorophyll", disabled=True, className="me-1"
            )
        ),
        dbc.NavItem(
            dbc.NavLink(className="bi bi-filter-circle-fill me-1", id="filter-by")
        ),
        dbc.NavItem(
            dbc.NavLink(href="#qc", className="bi bi-search me-1", id="qc-button")
        ),
        dbc.NavItem(
            dbc.NavLink(id="figure-menu-button", className="bi bi-file-bar-graph")
        ),
        dbc.NavItem(dbc.NavLink(className="bi bi-person-circle me-1", id="log-in")),
    ],
    className="ms-auto",
    # align="center",
)


def get_navbar(color, dark):
    @callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")],
    )
    def toggle_navbar_collapse(n, is_open):
        if n:
            return not is_open
        return is_open

    return dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    # Use row and col to control vertical alignment of logo / brand
                    dbc.Row(
                        [
                            dbc.Col(html.Img(src="assets/logo.png", height="40px")),
                            dbc.Col(
                                dbc.NavbarBrand("Quality Control"), className="ms-2"
                            ),
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
                    href="#",
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
        color=color,
        dark=dark,
    )
