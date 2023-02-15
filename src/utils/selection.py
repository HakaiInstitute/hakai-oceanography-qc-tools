import logging

import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Dash, Input, Output, State, callback, ctx, dash_table, dcc, html

# from pages.nutrients import get_flag_var
from tools import update_dataframe

variables_flag_mapping = {"no2_no3_um": "no2_no3_flag"}


def get_flag_var(var):
    return variables_flag_mapping.get(var, var + "_flag")


logger = logging.getLogger(__name__)

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
                        ]
                    )
                ),
                dash_table.DataTable(id="selected-data-table"),
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
    logger.debug("start selected_flag: %s", graphs_selected_flag)
    graphs_selected_flag = [graph for graph in graphs_selected_flag if graph]
    if not graphs_selected_flag:
        return previously_selected_flag
    logger.debug("selected data: %s", graphs_selected_flag)
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
        logger.debug("previously selected data: %s", previously_selected_flag)
        df_previous = pd.DataFrame(previously_selected_flag).set_index("hakai_id")
        df = update_dataframe(df_previous, df, on=["hakai_id"])
    return df.reset_index().to_dict("records")
