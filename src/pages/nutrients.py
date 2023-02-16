import logging

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, callback, dcc, html, ctx, ALL

logger = logging.getLogger(__name__)
dash.register_page(__name__)

from hakai_qc.flags import flag_color_map
from utils.tools import update_dataframe, load_config

variables_flag_mapping = {"no2_no3_um": "no2_no3_flag"}

config = load_config()


def get_flag_var(var):
    return variables_flag_mapping.get(var, var + "_flag")


layout = html.Div(
    children=[
        dbc.Button(
            "Timeseries", id=dict(page="nutrients", type="button", label="timeseries")
        ),
        dbc.Button(
            "PO4 Red-Field",
            id=dict(page="nutrients", type="button", label="po4-rf"),
        ),
        dbc.Button(
            "SiO2 Red-Field",
            id=dict(page="nutrients", type="button", label="sio2-rf"),
        ),
        dcc.Graph(id={"type": "graph", "page": "nutrients"}),
    ]
)


@callback(
    Output({"type": "graph", "page": "nutrients"}, "figure"),
    Output("main-graph-spinner", "data"),
    Input("dataframe", "data"),
    Input("variable", "value"),
    Input("selected-data-table", "data"),
    Input(dict(page="nutrients", type="button", label=ALL), "n_clicks"),
    Input("line-out-depth-selector", "value"),
)
def generate_figure(data, variable, selected_data, button_triggered, line_out_depths):
    if not data or not variable:
        logger.debug("no data or variable available")
        return None, None

    # transform data for plotting
    logger.info(
        "Generating %s figure for line_out_depths=%s", variable, line_out_depths
    )
    df = pd.DataFrame(data)
    
    if line_out_depths:
        df = df.query("line_out_depth in @line_out_depths").copy()
        
    # apply manual selection flags
    if selected_data:
        df = update_dataframe(
            df, pd.DataFrame(selected_data), on="hakai_id", how="left"
        )

    df.loc[:,get_flag_var(variable)] = df.loc[:,get_flag_var(variable)].fillna("UN")
    df.loc[:,"time"] = pd.to_datetime(df["collected"])
    df.loc[:,"year"] = df["time"].dt.year

    # determinate which plot type to generate
    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, str) or "label" not in triggered_id:
        triggered_id = {'label': 'default'}
    
    if triggered_id["label"] == "po4-rf":
        logger.debug("get po4 rf plot ")
        fig = get_red_field_plot(df, "po4", [2.1875, 35], 100)
    elif triggered_id["label"] == "sio2-rf":
        logger.debug("get sio2 rf plot ")
        fig = get_red_field_plot(df, "sio2", [32.8125, 35], 100)
    else:
        logger.debug("get default time series plot ")
        fig = px.line(
            df,
            x="collected",
            y=variable,
            color=get_flag_var(variable),
            symbol="quality_level",
            color_discrete_map=flag_color_map,
            hover_data=["hakai_id"],
            template="simple_white",
            labels=config['VARIABLES_LABEL']
        )
        for trace in fig.data:
            if "AV" not in trace['name'] and "UN" not in trace['name']:
                trace.mode = 'markers'

    if fig.layout.yaxis.title.text in ["pressure", "depth", "line_out_depth"]:
        fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=800, legend=dict(
    yanchor="top",
    y=0.99,
    xanchor="left",
    x=0.01,
    entrywidth=0.3, # change it to 0.3
    entrywidthmode='fraction'
))
    return fig, None


def get_red_field_plot(df, var, slope_limit, max_depth):
    figs = px.scatter(
        df.query(f"line_out_depth<{max_depth}"),
        x=var,
        y="no2_no3_um",
        color="line_out_depth",
        hover_data=["hakai_id", "date"],
        template="simple_white",
        title=config['VARIABLES_LABEL'][var],
        labels=config['VARIABLES_LABEL'],
        facet_col="year",
    )

    for id, item in enumerate(figs.data):
        figs.add_trace(
            go.Scatter(
                x=[0, slope_limit[0]],
                y=[0, slope_limit[1]],
                mode="lines",
                line_color="red",
                showlegend=False,
            ),
            row=1,
            col=id + 1,
        )
    return figs
