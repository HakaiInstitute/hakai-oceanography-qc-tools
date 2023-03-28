import logging

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, callback, ctx, dcc, html

logger = logging.getLogger(__name__)
dash.register_page(__name__)

from hakai_qc.flags import flag_color_map, get_hakai_variable_flag
from hakai_qc.nutrients import run_nutrient_qc
from utils.tools import load_config, update_dataframe

variables_flag_mapping = {"no2_no3_um": "no2_no3_flag"}
nutrient_variables = ["no2_no3_um", "sio2", "po4"]
config = load_config()


def get_flag_var(var):
    return variables_flag_mapping.get(var, var + "_flag")


figure_radio_buttons = dbc.RadioItems(
    id={"page": "nutrient", "type": "figure-type-selector"},
    className="btn-group",
    inputClassName="btn-check",
    labelClassName="btn btn-outline-primary",
    labelCheckedClassName="active",
    options=[
        {"label": "Time Series", "value": "timeseries"},
        {
            "label": "Time Series Profiles",
            "value": "timeseries-profiles",
        },
        {"label": "Contour Profiles", "value": "contour"},
        {"label": "PO4 red-field", "value": "po4-rf"},
        {"label": "SiO2 red-field", "value": "sio2-rf"},
    ],
    value="timeseries",
)
plot_inputs = dbc.Col(
    [
        dbc.InputGroup(
            [
                dbc.InputGroupText("Rows"),
                dbc.Select(
                    options=[
                        {"label": None, "value": None},
                        {"label": "Quality Level", "value": "quality_level"},
                        {"label": "Year", "value": "year"},
                    ],
                    value=None,
                    id="nutrients-facet-rows",
                ),
            ]
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText("Columns"),
                dbc.Select(
                    options=[
                        {"label": None, "value": None},
                        {"label": "Quality Level", "value": "quality_level"},
                        {"label": "Year", "value": "year"},
                    ],
                    value=None,
                    id="nutrients-facet-columns",
                ),
            ]
        ),
    ]
)

layout = html.Div(
    children=[
        dbc.Row(
            [
                dbc.Col(plot_inputs, width=2),
                dbc.Col(
                    figure_radio_buttons,
                    className="radio-group col-5 mx-auto",
                ),
                dbc.Col(
                    dbc.Button("Run Auto-QC", id="run-nutrient-auto-qc"),
                    width=2,
                ),
            ]
        ),
        dcc.Graph(id={"type": "graph", "page": "nutrients"}, figure={}),
        dcc.Store(id={"id": "selected-data", "source": "auto-qc"}),
    ]
)


@callback(
    Output({"type": "graph", "page": "nutrients"}, "figure"),
    Output("main-graph-spinner", "data"),
    Input("dataframe", "data"),
    Input("variable", "value"),
    Input("selected-data-table", "data"),
    Input({"page": "nutrient", "type": "figure-type-selector"}, "value"),
    Input("line-out-depth-selector", "value"),
    Input("nutrients-facet-columns", "value"),
    Input("nutrients-facet-rows", "value"),
)
def generate_figure(
    data,
    variable,
    selected_data,
    figure_type,
    line_out_depths,
    facet_col,
    facet_row,
):
    if not data or not variable:
        logger.debug("no data or variable available")
        return {}, None

    # transform data for plotting
    logger.info(
        "Generating %s figure for line_out_depths=%s", variable, line_out_depths
    )
    df = pd.DataFrame(data)
    px_kwargs = {"facet_col": facet_col, "facet_row": facet_row}
    px_kwargs = {
        key: value if value != "" else None for key, value in px_kwargs.items()
    }
    if line_out_depths and figure_type != "contour":
        df = df.query("line_out_depth in @line_out_depths").copy()

    # apply manual selection flags
    if selected_data:
        df = update_dataframe(
            df, pd.DataFrame(selected_data), on="hakai_id", how="left"
        )

    df.loc[:, get_flag_var(variable)] = df.loc[:, get_flag_var(variable)].fillna("UKN")
    df.loc[:, "time"] = pd.to_datetime(df["collected"])
    df.loc[:, "year"] = df["time"].dt.year

    # select plot to present based on triggered_id
    if figure_type == "po4-rf":
        logger.debug("get po4 rf plot ")
        fig = get_red_field_plot(df, "po4", [2.1875, 35], 100, px_kwargs)
    elif figure_type == "sio2-rf":
        logger.debug("get sio2 rf plot ")
        fig = get_red_field_plot(df, "sio2", [32.8125, 35], 100, px_kwargs)
    elif figure_type == "timeseries-profiles":
        fig = get_timeseries_plot(
            df,
            y="line_out_depth",
            color=variable,
            facet_col=px_kwargs["facet_col"],
            facet_row=px_kwargs["facet_row"],
        )
    elif figure_type == "contour":
        fig = get_contour(df, x="collected", y="line_out_depth", color=variable)
    else:
        logger.debug("get default time series plot for %s", figure_type)
        fig = get_timeseries_plot(
            df,
            y=variable,
            color=get_flag_var(variable),
            facet_col=px_kwargs["facet_col"],
            facet_row=px_kwargs["facet_row"],
        )

    fig.update_layout(
        height=600,
    )
    fig.update_layout(modebar=dict(color=config["NAVBAR_COLOR"]), dragmode="select")
    return fig, None


def get_red_field_plot(df, var, slope_limit, max_depth, px_kwargs):
    figs = px.scatter(
        df.query(f"line_out_depth<{max_depth}"),
        x=var,
        y="no2_no3_um",
        color="line_out_depth",
        hover_data=["hakai_id", "date"],
        template="simple_white",
        title=config["VARIABLES_LABEL"][var],
        labels=config["VARIABLES_LABEL"],
        **px_kwargs,
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


def get_timeseries_plot(df, **kwargs):
    default_inputs = dict(
        x="collected",
        color_discrete_map=flag_color_map,
        hover_data=["hakai_id", "line_out_depth"],
        labels=config["VARIABLES_LABEL"],
    )
    default_inputs.update(kwargs)
    logger.debug("Plot figure kwargs: %s", kwargs)
    fig = px.scatter(df, **default_inputs)

    for trace in fig.data:
        if "AV" not in trace["name"] and "UN" not in trace["name"]:
            trace.mode = "markers"
    if kwargs.get("y") in ["pressure", "depth", "line_out_depth"]:
        fig.update_yaxes(autorange="reversed")
    return fig


def get_contour(df, x, y, color, x_interp_limit=3, y_interp_limit=4):
    df_pivot = (
        pd.pivot_table(df, values=color, index=y, columns=x, aggfunc="mean")
        .interpolate(axis="index", limit=x_interp_limit)
        .sort_index(axis=0)
        .sort_index(axis=1)
        .interpolate(axis="columns", limit=y_interp_limit)
    )
    fig = go.Figure(
        data=go.Contour(
            z=df_pivot.values,
            x=df_pivot.columns,
            y=df_pivot.index.values,
            colorbar=dict(title=color, titleside="right"),
            colorscale="RdYlGn",
            ncontours=10,
            contours_coloring="heatmap"
            # ,connectgaps=True
        )
    )
    fig.update_yaxes(
        title=y,
        autorange="reversed",
        linecolor="black",
        mirror=True,
        ticks="outside",
        showline=True,
    )
    fig.update_xaxes(
        title=x, linecolor="black", mirror=True, ticks="outside", showline=True
    )
    return fig


@callback(
    Output({"id": "selected-data", "source": "auto-qc"}, "data"),
    Output("auto-qc-nutrient-spinner", "data"),
    State("dataframe", "data"),
    State("selected-data-table", "data"),
    Input("run-nutrient-auto-qc", "n_clicks"),
)
def run_nutrient_auto_qc(data, selected_data, n_clicks):
    logger.debug("Run nutrient auto qc")
    if data is None:
        logger.debug("No data to qc")
        return [], None
    df = pd.DataFrame(data).dropna(subset=nutrient_variables)
    # Convert collected to datetime object and ignore timezone
    df["collected"] = pd.to_datetime(df["collected"], utc=True).dt.tz_localize(None)
    pre_qc_df = df.copy()

    if selected_data:
        df = update_dataframe(
            df, pd.DataFrame(selected_data), on="hakai_id", how="left"
        )
    nutrient_variables_flags = [
        get_hakai_variable_flag(var) for var in nutrient_variables
    ]
    # Run QC
    df = run_nutrient_qc(df, overwrite_existing_flags=False)

    # Standardize flag tables
    df = df[["hakai_id"] + nutrient_variables_flags].groupby("hakai_id").first()
    pre_qc_df = (
        pre_qc_df[["hakai_id"] + nutrient_variables_flags].groupby("hakai_id").first()
    )

    # Compare prior and after qc results
    df_compare = df.compare(pre_qc_df).swaplevel(axis="columns")["self"]

    # Return just the flags that have been updated
    return (
        df_compare[nutrient_variables_flags].reset_index().to_dict("records"),
        None,
    )
