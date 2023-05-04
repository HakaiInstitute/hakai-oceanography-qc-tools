import logging
import re
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import ALL, MATCH, Input, Output, State, callback, ctx, dcc, html

from hakai_qc.nutrients import (
    variables_flag_mapping,
)
from hakai_qc.flags import flag_mapping

from utils.tools import load_config, update_dataframe

config = load_config()


logger = logging.getLogger(__name__)
FIGURE_GROUPS = ["Timeseries Profiles", "Profile"]

figure_radio_buttons = dbc.Row(
    [
        dbc.RadioItems(
            id="figure-type-selector",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            labelCheckedClassName="active",
        ),
    ],
    justify="center",
    align="center",
    className="radio-group",
)

figure_menu = dbc.Offcanvas(
    [
        html.H3("Figure Menu"),
        dbc.Row(
            [
                dbc.Col(dbc.Label("Label"), width=2),
                dbc.Col(
                    dbc.Input(
                        id={
                            "item": "label",
                            "group": "graph",
                            "options": "str",
                            "type": "input",
                        },
                        debounce=True,
                    ),
                    width=10,
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Label("Type"), width=2),
                dbc.Col(
                    dbc.Select(
                        id={
                            "item": "type",
                            "group": "graph",
                            "options": "predefined",
                            "type": "input",
                        },
                        options=[
                            {"label": key, "value": key}
                            for key in ["scatter", "contour"]
                        ],
                    ),
                    width=10,
                ),
            ],
            align="center",
        ),
        *[
            dbc.Row(
                [
                    dbc.Col(dbc.Label(item.title()), width=2),
                    dbc.Col(
                        dbc.Select(
                            id={
                                "item": item,
                                "group": "graph",
                                "options": "variables",
                                "type": "input",
                            }
                        ),
                        width=10,
                    ),
                ],
                align="center",
            )
            for item in ["x", "y", "color", "symbol"]
        ],
        html.Br(),
        dbc.Row(
            [
                dbc.Col(dbc.Label("Color Scale"), width=2),
                dbc.Col(
                    dbc.Select(
                        id={
                            "item": "color_continuous_scale",
                            "group": "graph",
                            "options": "color_continuous_scale",
                            "type": "input",
                        },
                        options=[
                            {"label": key, "value": key}
                            for key in px.colors.named_colorscales()
                        ],
                    ),
                    width=10,
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Label("Color Range"), width=2),
                dbc.Col(
                    dbc.Input(
                        placeholder="minimum",
                        type="number",
                        id={
                            "item": "color_min",
                            "group": "graph",
                            "options": "float",
                            "type": "input",
                        },
                    ),
                    width=5,
                ),
                dbc.Col(
                    dbc.Input(
                        placeholder="maximum",
                        type="number",
                        id={
                            "item": "color_max",
                            "group": "graph",
                            "options": "float",
                            "type": "input",
                        },
                    ),
                    width=5,
                ),
            ],
            align="center",
        ),
        html.Br(),
        *[
            dbc.Row(
                [
                    dbc.Col(dbc.Label(item.replace("_", " ").title()), width=2),
                    dbc.Col(
                        dbc.Select(
                            id={
                                "item": item,
                                "group": "graph",
                                "options": "variables",
                                "type": "input",
                            }
                        ),
                        width=10,
                    ),
                ]
            )
            for item in ["facet_col", "facet_row"]
        ],
        html.Br(),
        dbc.Row(
            [
                dbc.Col(dbc.Label("Hori. Line"), width=2),
                dbc.Col(
                    dbc.Input(
                        id={
                            "item": "hline",
                            "group": "graph",
                            "options": "str",
                            "type": "input",
                        },
                        type="char",
                        debounce=True,
                    ),
                    width=10,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Label("Vert. Line"), width=2),
                dbc.Col(
                    dbc.Input(
                        id={
                            "item": "vline",
                            "group": "graph",
                            "options": "str",
                            "type": "input",
                        },
                        debounce=True,
                        type="char",
                    ),
                    width=10,
                ),
            ]
        ),
        dbc.Button(
            "Update",
            color="primary",
            id="update-figure",
            className="me-1",
        ),
    ],
    id="figure-menu",
    is_open=False,
)


def get_color_range(var, prc=[0.02, 0.98]):
    return var.quantile(prc).values


def get_contour(df, x, y, color, range_color=None, x_interp_limit=3, y_interp_limit=4):
    df_pivot = (
        pd.pivot_table(df, values=color, index=y, columns=x, aggfunc="mean")
        .interpolate(axis="index", limit=x_interp_limit)
        .sort_index(axis=0)
        .sort_index(axis=1)
        .interpolate(axis="columns", limit=y_interp_limit)
    )
    min_color, max_color = get_color_range(df[color])
    if range_color:
        min_color = range_color[0] or min_color
        max_color = range_color[1] or max_color

    fig = go.Figure(
        data=go.Contour(
            z=df_pivot.values,
            x=df_pivot.columns,
            y=df_pivot.index.values,
            colorbar=dict(title=color, titleside="right"),
            colorscale="RdYlGn",
            contours=dict(
                start=min_color,
                end=max_color,
                size=(max_color - min_color) / 10,
            ),
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


def get_flag_var(var, variables):
    if var is None:
        return
    if var in flag_mapping:
        return flag_mapping[var]
    elif var + "_flag_level_1" in variables:
        return variables_flag_mapping.get(var, var + "_flag_level_1")
    return variables_flag_mapping.get(var, var + "_flag")


@callback(
    Output({"type": "graph", "page": "main"}, "figure"),
    Output("main-graph-spinner", "data"),
    State("dataframe", "data"),
    State("variable", "value"),
    Input("selected-data-table", "data"),
    Input({"type": "dataframe-subset", "subset": ALL}, "placeholder"),
    Input({"type": "dataframe-subset", "subset": ALL}, "value"),
    State({"item": ALL, "group": "graph", "options": ALL, "type": ALL}, "id"),
    State({"item": ALL, "group": "graph", "options": ALL, "type": ALL}, "value"),
    State({"item": ALL, "group": "graph", "options": ALL, "type": ALL}, "placeholder"),
    Input("update-figure", "n_clicks"),
    Input("figure-menu-label-spinner", "data"),
)
def generate_figure(
    data,
    variable,
    selected_data,
    subset_vars,
    subsets,
    input_ids,
    input_values,
    input_defaults,
    update_figure,
    figure_menu_spinner,
):
    # transform data for plotting
    if data is None:
        return None, None
    logger.info(
        "Generating %s figure for subsets=%s", variable, zip(subset_vars, subsets)
    )
    df = pd.DataFrame(data)
    filter_subsets = " and ".join(
        [
            f"{subset_var} in {subset}" if subset_var != "Filter data ..." else subset
            for subset_var, subset in zip(subset_vars, subsets)
            if subset
        ]
    )

    if filter_subsets:
        logger.debug("filter data with: %s", filter_subsets)
        df = df.query(filter_subsets)

    # apply manual selection flags
    if selected_data:
        df = update_dataframe(
            df, pd.DataFrame(selected_data), on="hakai_id", how="left"
        )
    time_var = "collected" if "collected" in df else "start_dt"
    # df.loc[:, get_flag_var(variable)] = df.loc[:, get_flag_var(variable)].fillna("UKN")
    df[time_var] = pd.to_datetime(df[time_var])
    df.loc[:, "year"] = df[time_var].dt.year

    logger.debug("data to plot len(df)=%s", len(df))
    # Define plotly express parameters
    placeholder_to_null = {"minimum": None, "maximum": None}
    px_kwargs = {
        key["item"]: input_value
        or placeholder_to_null.get(input_default, input_default)
        for key, input_value, input_default in zip(
            input_ids, input_values, input_defaults
        )
    }

    if px_kwargs.get("x") is None or px_kwargs.get("y") is None:
        logger.debug("No x or y axis given: px_kwargs=%s", px_kwargs)
        return None, None

    label = px_kwargs.pop("label")
    plot_type = px_kwargs.pop("type")

    # Sort range_color
    range_color = [
        px_kwargs.pop("color_min"),
        px_kwargs.pop("color_max"),
    ]

    vline = px_kwargs.pop("vline")
    hline = px_kwargs.pop("hline")
    px_kwargs = {
        key: value for key, value in px_kwargs.items() if value not in (None, "None")
    }

    if plot_type == "scatter":
        px_kwargs["labels"] = config["VARIABLES_LABEL"]
        if range_color[0] is not None and range_color[1] is not None:
            logger.debug("apply range_color=%s", range_color)
            # px_kwargs["range_color"] = range_color
        logger.debug("Generate scatter: %s", str(px_kwargs))
        fig = px.scatter(df, **px_kwargs)
    elif plot_type == "contour":
        logger.debug("Generate contour: %s", px_kwargs)
        fig = get_contour(df, **px_kwargs)
    else:
        logger.error("unknown plot_type=%s", plot_type)
        return None, None

    fig.for_each_trace(
        lambda t: t.update(name=config["VARIABLES_LABEL"].get(t.name, t.name))
    )
    fig.update_layout(
        height=600,
    )
    if re.search("profile", label, re.IGNORECASE):
        fig.update_yaxes(autorange="reversed")
    fig.update_layout(modebar=dict(color=config["NAVBAR_COLOR"]), dragmode="select")
    logger.debug("output figure: %s", fig)
    return fig, None


@callback(
    Output(
        {"item": ALL, "group": ALL, "options": "variables", "type": "input"}, "options"
    ),
    State(
        {"item": ALL, "group": ALL, "options": "variables", "type": "input"}, "options"
    ),
    Input("dataframe-variables", "data"),
)
def define_variables_options(n, variables):
    if variables is None:
        return len(n) * [None]
    variables = [
        {"label": config["VARIABLES_LABEL"].get(variable, variable), "value": variable}
        for variable in variables.split(",")
    ]
    variables = [{"label": "None", "value": "None"}] + variables
    return len(n) * [variables]


@callback(
    {
        "type": Output(
            {
                "item": "type",
                "group": "graph",
                "options": "predefined",
                "type": "input",
            },
            "placeholder",
        ),
        "x": Output(
            {"item": "x", "group": "graph", "options": "variables", "type": "input"},
            "placeholder",
        ),
        "y": Output(
            {"item": "y", "group": "graph", "options": "variables", "type": "input"},
            "placeholder",
        ),
        "color": Output(
            {
                "item": "color",
                "group": "graph",
                "options": "variables",
                "type": "input",
            },
            "placeholder",
        ),
        "symbol": Output(
            {
                "item": "symbol",
                "group": "graph",
                "options": "variables",
                "type": "input",
            },
            "placeholder",
        ),
    },
    Output("figure-menu-label-spinner", "data"),
    Input(
        {"item": "label", "group": "graph", "options": "str", "type": "input"},
        "value",
    ),
    State("variable", "value"),
    State("dataframe-variables", "data"),
    State("location", "pathname"),
)
def define_graph_default_values(label, variable, variables, path):
    placeholders = dict(type=None, x=None, y=None, color=None, symbol=None)
    if variable is None or label is None:
        return default_placeholders, None

    # Apply presets
    logger.debug("Find present for path=%s; label=%s", path, label)
    if path in figure_presets and label in figure_presets[path]:
        logger.debug("Apply figure preset: %s -> %s", path, label)
        placeholders.update(figure_presets[path][label])
    # replace main_var
    variable_placeholers = {
        "main_var": variable,
        "main_var_flag": get_flag_var(variable, variables.split(",")),
    }
    placeholders = {
        key: variable_placeholers.get(value, value)
        for key, value in placeholders.items()
    }
    logger.debug(
        "Set presets: path=%s, label=%s, placeholders=%s", path, label, placeholders
    )
    return placeholders, None


@callback(
    Output(
        {
            "item": "label",
            "group": "graph",
            "options": "str",
            "type": "input",
        },
        "value",
    ),
    Input("figure-type-selector", "value"),
    Input("dataframe-variables", "data"),
)
def get_label(label, variables):
    if variables is None:
        return None
    logger.debug("Selected figure type preset: %s", label)
    return label


@callback(
    Output("figure-type-selector", "options"),
    Output("figure-type-selector", "value"),
    Input("location", "pathname"),
)
def get_plot_types(path):
    if path == "/":
        return None, None
    presets = [
        {"label": item, "value": item} for item in figure_presets.get(path, {}).keys()
    ]
    return presets, presets[0]["value"]


default_placeholders = dict(type=None, x=None, y=None, color=None, symbol=None)
figure_presets = {
    "/nutrients": {
        "Time Series": {
            "type": "scatter",
            "x": "collected",
            "y": "main_var",
            "color": "main_var_flag",
        },
        "Time Series Profiles": {
            "type": "scatter",
            "x": "collected",
            "y": "line_out_depth",
            "color": "main_var",
            "symbol": "main_var_flag",
        },
        "Contour Profiles": {
            "type": "contour",
            "x": "collected",
            "y": "line_out_depth",
            "color": "main_var",
        },
        "PO4 red-field": {
            "type": "scatter",
            "x": "po4",
            "y": "main_var",
            "color": "main_var_flag",
        },
        "SiO2 red-field": {
            "type": "scatter",
            "x": "sio2",
            "y": "main_var",
            "color": "main_var_flag",
        },
    },
    "/ctd": {
        "Time Series Profiles": {
            "type": "scatter",
            "x": "start_dt",
            "y": "depth",
            "color": "main_var",
            "symbol": "main_var_flag",
        },
        "Time Series": {
            "type": "scatter",
            "x": "start_dt",
            "y": "main_var",
            "color": "main_var_flag",
        },
        "Contour Profiles": {
            "type": "contour",
            "x": "start_dt",
            "y": "pressure",
            "color": "main_var",
        },
    },
}
