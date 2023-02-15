import logging

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, callback, dcc

logger = logging.getLogger(__name__)


@callback(Output("main-graph", "figure"), Input("dataframe", "data"))
def generate_figure(data, x="collected", y="line_out_depth"):
    logger.info("Generating figure")
    if not data:
        return
    df = pd.DataFrame(data)
    logger.debug("dataframe containes %s rows", len(df))
    fig = px.scatter(df, x="collected", y="line_out_depth", color="sio2")
    return fig
