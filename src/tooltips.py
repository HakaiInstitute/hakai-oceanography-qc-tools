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
    ]
)
