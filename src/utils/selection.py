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
    # filter_action="native",
    page_size=15,
    sort_action="native",
    # row_selectable="multi",
    # column_selectable="single",
    fixed_columns={"headers": True, "data": 2},
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
        "minWidth": 100,
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
                            ),
                            dbc.Button("Apply Flag", id="apply-selection-flag"),
                            dbc.Button("Download .xlsx", id="download-qc-excel-button"),
                            dcc.Download(id="download-qc-excel"),
                        ]
                    )
                ),
                selection_table,
            ],
            is_open=True,
            id="selection-interface",
        ),
    ]
)


@callback(
    Output("selection-interface", "is_open"),
    Input({"type": "graph", "page": ALL}, "selectedData"),
    Input("show-selection", "n_clicks"),
    State("selection-interface", "is_open"),
)
def show_selection_interace(graph_selectedData, show_selection, is_open):
    trigger = ctx.triggered_id
    if trigger == "show-selection":
        return not is_open
    return bool([selection for selection in graph_selectedData if selection])


@callback(
    Output("selected-data-table", "data"),
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
    Input("download-qc-excel-button", "n_clicks"),
    State("selected-data-table", "data"),
    State("location", "pathname"),
)
def get_qc_excel(n_clicks, data,location):
    """Save file to an excel file format compatible with the Hakai Portal upload"""
    logger.info("Generate excel file")
    if data is None:
        return None
    df = pd.DataFrame(data).drop(
        columns=["id", "start_depth", "target_depth_m", "bottle_drop", "collected"],
        errors="ignore",
    )

    if not os.path.exists(config["TEMP_FOLDER"]):
        os.makedirs(config["TEMP_FOLDER"])
    temp_file = os.path.join(
        config["TEMP_FOLDER"],
        f"hakai-qc-{location[1:]}-{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}.xlsx",
    )
    temp_dir = os.path.dirname(temp_file)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    shutil.copy(
        os.path.join(MODULE_PATH, f"../assets/hakai-template-{location[1:]}-samples.xlsx"), temp_file
    )
    with pd.ExcelWriter(
        temp_file, engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        df.to_excel(writer, sheet_name="Hakai Data")
    logger.info("Upload Hakai QC excel file")
    return dcc.send_file(temp_file)
