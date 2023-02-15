import logging

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, callback, dcc, html

logger = logging.getLogger(__name__)
dash.register_page(__name__)

from hakai_qc.flags import flag_color_map

df = pd.DataFrame(
    {
        "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
        "Amount": [4, 1, 2, 2, 4, 5],
        "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"],
    }
)

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

variables_flag_mapping = {"no2_no3_um": "no2_no3_flag"}


def get_flag_var(var):
    return variables_flag_mapping.get(var, var + "_flag")


layout = html.Div(
    children=[
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
            ],
            is_open=True,
            id="selection-interface",
        ),
        dbc.Select(options=["sio2", "po4", "no2_no3_um"], value="sio2", id="variable"),
        dcc.Graph(id={"type":"graph","page":"nutrients"}, figure=fig),
    ]
)


def merge_data_and_selection(df, selection, index_by="hakak_id"):
    if not selection:
        return df
    logger.debug("selection to add [%s] %s", type(selection), selection)
    df_sel = pd.DataFrame(selection)
    logger.debug("selection df_se['hakai_id']: %s", df_sel["hakai_id"])
    df_sel = df_sel.set_index(index_by)
    original_indexes = df.index.names
    df = df.reset_index(index_by)
    df.update(df_sel)
    return df.reset_index(original_indexes)


@callback(
    Output({"type":"graph","page":"nutrients"}, "figure"),
    Output("main-graph-spinner", "data"),
    Input("dataframe", "data"),
    Input("variable", "value"),
    Input("selected-data-table", "data"),
)
def generate_figure(data, y, selected_data):
    logger.info("Generating figure")
    if not data:
        return None, None
    df = pd.DataFrame(data)
    if selected_data:
        df = merge_data_and_selection(df, selected_data)

    df[get_flag_var(y)] = df[get_flag_var(y)].fillna("UN")
    fig = px.scatter(
        df,
        x="collected",
        y=y,
        color=get_flag_var(y),
        color_discrete_map=flag_color_map,
        hover_data=["hakai_id"],
    )
    fig.update_yaxes(autorange="reversed")
    return fig, None


@callback(Output("selection-interface", "is_open"), Input("main-graph", "selectedData"))
def show_selection_interace(selectedData):
    return True if selectedData else False


@callback(
    Output("selected-data-table", "data"),
    Input("apply-selection-flag", "n_clicks"),
    State({"type":"graph","page":"nutrients"}, "selectedData"),
    State("selected-data-table", "data"),
    State("selection-flag", "value"),
    State("variable", "value"),
)
def add_flag_selection(
    click, selected_flag, previously_selected_flag, flag_to_apply, variable
):
    if not selected_flag:
        return previously_selected_flag
    logger.debug("selected data: %s", selected_flag)
    df = pd.DataFrame(
        [
            {
                "hakai_id": point["customdata"][0],
                variables_flag_mapping.get(variable, variable + "_flag"): flag_to_apply,
            }
            for point in selected_flag["points"]
        ]
    ).set_index("hakai_id")

    if previously_selected_flag:
        logger.debug("previously selected data: %s", previously_selected_flag)
        df_previous = pd.DataFrame(previously_selected_flag).set_index("hakai_id")
        df = update_dataframe(df_previous, df, on=["hakai_id"])
    return df.reset_index().to_dict("records")


def update_dataframe(df, new_df, on=None, suffix="_new"):
    """Merge two dataframes on specified columns and update
    missing values from the second dataframe by the first one."""
    # Compbine the two dataframes
    df_merge = pd.merge(df, new_df, how="outer", suffixes=("", suffix), on=on)

    # merge columns
    drop_cols = []
    for new_col in [col for col in df_merge.columns if col.endswith(suffix)]:
        col = new_col[:-4]
        df_merge[col] = df_merge[new_col].fillna(df_merge[col])
        drop_cols += [new_col]
    df_merge.drop(columns=drop_cols, inplace=True)
    return df_merge
