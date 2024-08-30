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
        dbc.Tooltip(
            "User initials to include in data qc (all capital with 2 to 10 letters, ex: 'AB')",
            target="user-initials",
        ),
        dbc.Tooltip(
            "Apply to selection! Initials should be present to activate this button.",
            target="selection-apply-button",
        ),
        dbc.Tooltip(
            "Update qc table modified columns (this is useful when manual corrections are made directely on the table itself)",
            target="update-qc-table",
        ),
        dbc.Tooltip(
            "Clear hakai_id selection filter in qc-table",
            target="clear-selected-row-table",
        ),
        dbc.Tooltip(
            "Download Excel file with QC data",
            target="download-qc-excel-button",
        ),
        dbc.Tooltip(
            "Upload Excel file with QC data directly to the hakai database",
            target="upload-to-hakai-button",
        ),
    ]
)
