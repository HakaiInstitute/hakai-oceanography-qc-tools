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
        dbc.Button('Timeseries',id=dict(page='nutrients',type="button",label="timeseries")),
        dbc.Button('Show PO4 red field',id=dict(page='nutrients',type="button",label="po4-rf")),
        dbc.Button('Show SiO2 red field',id=dict(page='nutrients',type="button",label="sio2-rf")),
        dcc.Graph(id={"type": "graph", "page": "nutrients"}),
    ]
)


@callback(
    Output({"type": "graph", "page": "nutrients"}, "figure"),
    Output("main-graph-spinner", "data"),
    Input("dataframe", "data"),
    Input("variable", "value"),
    Input("selected-data-table", "data"),
    Input(dict(page='nutrients',type="button",label=ALL),"n_clicks"),
)
def generate_figure(data, y, selected_data,button_triggered):
    logger.info("Generating figure")
    if not data:
        return None, None
    df = pd.DataFrame(data)
    if selected_data:
        df = update_dataframe(
            df, pd.DataFrame(selected_data), on="hakai_id", how="left"
        )
    df[get_flag_var(y)] = df[get_flag_var(y)].fillna("UN")
    df['time'] = pd.to_datetime(df['collected'])
    df['year'] = df['time'].dt.year

    triggered_id = ctx.triggered_id
    if isinstance(triggered_id,str) or 'label' not in triggered_id:
        pass
    elif triggered_id['label']=='po4-rf':
        return get_red_field_plot(df,'po4',[2.1875,35],100), None
    elif triggered_id['label']=='sio2-rf':
        return get_red_field_plot(df,'sio2',[32.8125,35],100),None

    fig = px.scatter(
        df,
        x="collected",
        y=y,
        color=get_flag_var(y),
        symbol="quality_level",
        color_discrete_map=flag_color_map,
        hover_data=["hakai_id"],
        template="simple_white",
    )
    if fig.layout.yaxis.title.text in ["pressure", "depth", "line_out_depth"]:
        fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=800)
    return fig, None


def get_red_field_plot(df, var, slope_limit, max_depth):
    labels = {
        "sio2": f"SiO2 (uM)",
        "po4": "PO4 (uM)",
        "line_out_depth": "Bottle Target Depth (m)",
    }
    figs = px.scatter(
        df.query("line_out_depth<@max_depth"),
        x=var,
        y="no2_no3_um",
        color="line_out_depth",
        hover_data=["hakai_id", "date"],
        template="simple_white",
        title=labels[var],
        labels=labels,
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


