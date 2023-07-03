import dash_bootstrap_components as dbc
from dash import html

tooltips = html.Div(
    [
        dbc.Tooltip(
            "Filter data by",
            target="filter-by",
        ),
        dbc.Tooltip(
            "Open/Close QC Flags Section",
            target="qc-button",
        ),
        dbc.Tooltip(
            "Hakai Login",
            target="log-in",
        ),
        dbc.Tooltip("Figure menu", target="figure-menu-button"),
        dbc.Tooltip("Move time filter to prior", target="filter-time-button-move-down"),
        dbc.Tooltip(
            "Move time filter range to after", target="filter-time-button-move-down"
        ),
    ]
)
