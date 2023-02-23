import logging
import shutil
import os
from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Dash, Input, Output, State, callback, ctx, dash_table, dcc, html

# from pages.nutrients import get_flag_var
from utils.tools import update_dataframe, load_config

config = load_config()
variables_flag_mapping = {"no2_no3_um": "no2_no3_flag"}
MODULE_PATH = os.path.dirname(__file__)


def get_flag_var(var):
    return variables_flag_mapping.get(var, var + "_flag")


logger = logging.getLogger(__name__)
selection_table = dash_table.DataTable(
    id="selected-data-table",
    page_size=40,
    sort_action="native",
    row_deletable=True,
    style_header={
        "fontWeight": "bold",
        "fontSize": "15px",
        "backgroundColor": config["NAVBAR_COLOR"],
        "color": "white",
        "textAlign": "center",
    },
    style_cell={
        # all three widths are needed
        "overflow": "hidden",
        "textOverflow": "ellipsis",
        "width": 150,
        "textAlign": "center",
        "fontSize": "14px",
    },
    style_cell_conditional=[
        {
            "if": {"column_id": "hakai_id"},
            "textAlign": "left",
            "backgroundColor": config["NAVBAR_COLOR"],
            "color": "white",
        }
    ],
    style_table={"minWidth": "200px", "float": "center"},
)
selection_interface = html.Div(
    [
        dbc.Collapse(
            [
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Apply flag to selection"),
                            dbc.Select(
                                options=["AV", "SVC", "SVD"],
                                value="AV",
                                id="selection-flag",
                                size="sm",
                                className="apply-flag-selector",
                            ),
                            dbc.Button("Apply Flag", id="apply-selection-flag"),
                        ],
                    ),
                    className="apply-flag-section",
                ),
                dbc.Button(
                    html.Div(
                        [
                            "Download .xlsx",
                            dbc.Spinner(
                                html.Div(id="hakai-excel-load-spinner"), size="lg"
                            ),
                        ]
                    ),
                    id="download-qc-excel-button",
                ),
                dcc.Download(id="download-qc-excel"),
                selection_table,
            ],
            is_open=True,
            id="selection-interface",
        ),
        dcc.Store(id={"id": "selected-data", "source": "figure"}),
    ]
)


@callback(
    Output("selection-interface", "is_open"),
    Input("selected-data-table", "data"),
    Input("show-selection", "n_clicks"),
    State("selection-interface", "is_open"),
)
def show_selection_interace(selected_data_table, show_selection, is_open):
    trigger = ctx.triggered_id
    if trigger == "show-selection":
        return not is_open
    return bool(selected_data_table)


@callback(
    Output("selected-data-table", "data"),
    State("selected-data-table", "data"),
    Input({"id": "selected-data", "source": ALL}, "data"),
)
def update_selected_data(selected_data, newly_selected):
    logger.debug(
        "updated selection data: selected=%s, newly_selected=%s",
        selected_data,
        newly_selected,
    )
    newly_selected =  [pd.DataFrame(source) for source in newly_selected if source is not None  and len(source)>0]
    if not selected_data and not newly_selected:
        logger.debug("no selection exist")
        return []
    if not selected_data:
        logger.debug("add a new selection to an empty list %s", newly_selected)
        return pd.concat(newly_selected).to_dict("records")

    logger.debug("append to a selection")
    for source in newly_selected:
        selected_data.update(pd.DataFrame(source), on="hakai_id", how="outer")
    return selected_data.reset_index().to_dict("records")


@callback(
    Output({"id": "selected-data", "source": "figure"}, "data"),
    Input("apply-selection-flag", "n_clicks"),
    State({"type": "graph", "page": ALL}, "selectedData"),
    State("selected-data-table", "data"),
    State("selection-flag", "value"),
    State("variable", "value"),
)
def add_flag_selection(
    click, graphs_selected_flag, previously_selected_flag, flag_to_apply, variable
):
    graphs_selected_flag = [graph for graph in graphs_selected_flag if graph]
    if not graphs_selected_flag:
        return previously_selected_flag

    df = pd.DataFrame(
        [
            {
                "hakai_id": point["customdata"][0],
                variables_flag_mapping.get(variable, variable + "_flag"): flag_to_apply,
            }
            for graph in graphs_selected_flag
            for point in graph["points"]
        ]
    ).set_index("hakai_id")

    if previously_selected_flag:
        df_previous = pd.DataFrame(previously_selected_flag).set_index("hakai_id")
        df = update_dataframe(df_previous, df, on=["hakai_id"])
    return df.reset_index().to_dict("records")


@callback(
    Output("download-qc-excel", "data"),
    Output("hakai-excel-load-spinner", "children"),
    Input("download-qc-excel-button", "n_clicks"),
    State("selected-data-table", "data"),
    State("location", "pathname"),
)
def get_qc_excel(n_clicks, data, location):
    """Save file to an excel file format compatible with the Hakai Portal upload"""
    logger.info("Generate excel file")
    if data is None:
        return None, None
    df = pd.DataFrame(data).drop(
        columns=["id", "start_depth", "target_depth_m", "bottle_drop", "collected"],
        errors="ignore",
    )
    temp_file = os.path.join(
        config["TEMP_FOLDER"],
        f"hakai-qc-{location[1:]}-{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}.xlsx",
    )
    logger.debug("Make a copy from the %s template", location[1:])
    shutil.copy(
        os.path.join(
            MODULE_PATH, f"../assets/hakai-template-{location[1:]}-samples.xlsx"
        ),
        temp_file,
    )
    logger.debug("Add data to qc excel file")
    with pd.ExcelWriter(
        temp_file, engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        df.to_excel(writer, sheet_name="Hakai Data", index=False)
    logger.info("Upload Hakai QC excel file")
    return dcc.send_file(temp_file), None
