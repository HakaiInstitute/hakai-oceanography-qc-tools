import logging

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, callback, dcc, html

logger = logging.getLogger(__name__)
dash.register_page(__name__)

from hakai_qc.flags import flag_color_map
from tools import update_dataframe


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
        dcc.Graph(id={"type": "graph", "page": "nutrients"}, figure=fig),
    ]
)


@callback(
    Output({"type": "graph", "page": "nutrients"}, "figure"),
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
        df = update_dataframe(
            df, pd.DataFrame(selected_data), on="hakai_id", how="left"
        )

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
