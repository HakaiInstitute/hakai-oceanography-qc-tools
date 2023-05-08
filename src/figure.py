import json
import logging
import os
import re

import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import ALL, MATCH, Input, Output, State, callback, ctx, dcc, html

from download_hakai import fill_hakai_flag_variables
from hakai_qc.flags import flag_color_map, flag_mapping
from hakai_qc.nutrients import variables_flag_mapping
from utils import load_config, update_dataframe

config = load_config()
figure_presets_path = os.path.join(
    os.path.dirname(__file__), "assets/figure_presets.json"
)
with open(figure_presets_path) as file_handle:
    figure_presets = json.load(file_handle)

logger = logging.getLogger(__name__)
FIGURE_GROUPS = ["Timeseries Profiles", "Profile"]

figure_radio_buttons = html.Div(
    [
        dbc.Col(
            dbc.RadioItems(
                id="figure-type-selector",
                className="btn-group",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-primary",
                labelCheckedClassName="active",
                label_checked_style={
                    "background-color": "#B52026",
                    "color": "white",
                },
                label_style={"color": "#B52026"},
            ),
            width="auto",
        ),
        dbc.Col(
            dbc.Button(id="figure-menu-button", className="bi bi-plus figure-button"),
            width=1,
        ),
    ],
    className="radio-group",
)

figure_menu = dbc.Collapse(
    dbc.Card(
        [
            dbc.CardHeader("Figure Menu"),
            dbc.Row(
                [
                    dbc.Col(
                        [
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
                        ],
                        className="figure-menu-column",
                    ),
                    dbc.Col(
                        [
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
                                    dbc.Col(dbc.Label("Range Color"), width=2),
                                    dbc.Col(dbc.Label("Min"), width=1),
                                    dbc.Col(
                                        dbc.Input(
                                            type="number",
                                            id={
                                                "item": "color_min",
                                                "group": "graph",
                                                "options": "float",
                                                "type": "input",
                                            },
                                        ),
                                        width=4,
                                    ),
                                    dbc.Col(dbc.Label("Max"), width=1),
                                    dbc.Col(
                                        dbc.Input(
                                            type="number",
                                            id={
                                                "item": "color_max",
                                                "group": "graph",
                                                "options": "float",
                                                "type": "input",
                                            },
                                        ),
                                        width=4,
                                    ),
                                ],
                                align="center",
                            ),
                            html.Br(),
                            dbc.Row(
                                [
                                    dbc.Col(dbc.Label("Hover data"), width=2),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id={
                                                "item": "hover_data",
                                                "group": "graph",
                                                "options": "variables",
                                                "type": "input",
                                            },
                                            multi=True,
                                            clearable=True,
                                        ),
                                        width=10,
                                    ),
                                ],
                                align="center",
                            ),
                            *[
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label(item.replace("_", " ").title()),
                                            width=2,
                                        ),
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
                                    dbc.Col(dbc.Label("Extra traces"), width=2),
                                    dbc.Col(
                                        dbc.Input(
                                            id={
                                                "item": "extra_traces",
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
                        ],
                        className="figure-menu-column",
                    ),
                ]
            ),
            html.Div(
                dbc.Button("Update Figure", id="update-figure"),
                className="d-grid gap-2 col-6 mx-auto update-figure-button",
            ),
        ],
    ),
    id="figure-menu",
    is_open=False,
    className="data-selection-interface",
)


def get_color_range(var, prc=[0.02, 0.98]):
    min_limit, max_limit = var.quantile(prc).values
    return np.floor(10 * min_limit) / 10, np.ceil(10 * max_limit) / 10


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
    Input("selected-data-table", "data"),
    Input({"type": "dataframe-subset", "subset": ALL}, "placeholder"),
    Input({"type": "dataframe-subset", "subset": ALL}, "value"),
    {
        "id": State({"item": ALL, "group": "graph", "options": ALL, "type": ALL}, "id"),
        "value": State(
            {"item": ALL, "group": "graph", "options": ALL, "type": ALL}, "value"
        ),
        "default": State(
            {"item": ALL, "group": "graph", "options": ALL, "type": ALL}, "placeholder"
        ),
    },
    Input("update-figure", "n_clicks"),
    Input("figure-menu-label-spinner", "data"),
)
def generate_figure(data, selected_data, subset_vars, subsets, form_inputs, *args):
    def _add_extra_traces(extra_traces):
        if extra_traces is None:
            return
        for go_object, trace in (
            json.loads(extra_traces) if isinstance(extra_traces, str) else extra_traces
        ):
            if go_object == "Scatter":
                fig.add_trace(go.Scatter(**trace))

    # transform data for plotting
    if data is None or not any(form_inputs.get("default")):
        logger.debug("do not generate plot yet")
        return None, None

    # Parse figure-menu inputs
    px_kwargs_inputs = [
        "x",
        "y",
        "color",
        "symbol",
        "facet_col",
        "facet_row",
        "color_continuous_scale",
        "hover_data",
    ]
    logger.debug("sort figure-menu form input")
    form_inputs = pd.DataFrame(form_inputs)
    form_inputs = (
        form_inputs.assign(
            name=form_inputs["id"].apply(lambda x: x["item"]),
            output=form_inputs["value"].fillna(form_inputs["default"]),
        )
        .set_index("name")
        .replace({"None": None})
    )
    logger.debug("form inputs=\n%s", form_inputs)
    inputs = form_inputs["output"]

    px_kwargs = inputs[px_kwargs_inputs].dropna().to_dict()
    px_kwargs["hover_data"] = (
        px_kwargs["hover_data"].split(",")
        if isinstance(px_kwargs.get("hover_data"), str)
        else px_kwargs["hover_data"]
    )
    if px_kwargs.get("x") is None or px_kwargs.get("y") is None:
        logger.debug("No x or y axis given: px_kwargs=%s", px_kwargs)
        return None, None

    label = inputs["label"]
    plot_type = inputs["type"]
    if inputs[["color_min", "color_max"]].notna().any():
        range_color = inputs[["color_min", "color_max"]].tolist()
        logger.debug("set range color: %s", range_color)
        px_kwargs["range_color"] = range_color

    logger.debug("px_kwarkgs= %s", px_kwargs)
    # Get Data and filter by given subset
    logger.info("Generating figure for subsets=%s", list(zip(subset_vars, subsets)))
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

    # tranform data
    df = fill_hakai_flag_variables(df)
    time_var = "collected" if "collected" in df else "start_dt"
    df[time_var] = pd.to_datetime(df[time_var])
    df.loc[:, "year"] = df[time_var].dt.year
    logger.debug("data to plot len(df)=%s", len(df))

    # Generate plot
    if plot_type == "scatter":
        px_kwargs["labels"] = config["VARIABLES_LABEL"]
        if "flag" in px_kwargs.get("color"):
            logger.debug("assign color map for object")
            df[px_kwargs["color"]] = df[px_kwargs["color"]].astype(str)
            px_kwargs["color_discrete_map"] = flag_color_map

        logger.debug("Generate scatter: %s", str(px_kwargs))
        fig = px.scatter(df, **px_kwargs)
    elif plot_type == "contour":
        hover_data = px_kwargs.pop("hover_data", None)
        logger.debug("Generate contour: %s", px_kwargs)
        fig = get_contour(df, **px_kwargs)
    elif plot_type == "scatter_mapbox":
        fig = px.scatter_mapbox(
            df,
            lat=px_kwargs.pop("y"),
            lon=px_kwargs.pop("x"),
            **px_kwargs,
            size_max=15,
            zoom=10,
            height=600,
        )
        fig.update_layout(mapbox_style="open-street-map")
    else:
        logger.error("unknown plot_type=%s", plot_type)
        return None, None

    _add_extra_traces(inputs["extra_traces"] or "[]")

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
    Output(
        {
            "item": MATCH,
            "group": "graph",
            "options": MATCH,
            "type": "input",
        },
        "placeholder",
    ),
    State("location", "pathname"),
    Input(
        "figure-type-selector",
        "value",
    ),
    State(
        {
            "item": MATCH,
            "group": "graph",
            "options": MATCH,
            "type": "input",
        },
        "id",
    ),
    Input("variable", "value"),
    State("dataframe-variables", "data"),
)
def define_graph_default_values(path, label, parameter, variable, variables):
    if variable is None or label is None:
        return None
    path = path.split("/")[1]
    placeholder = figure_presets[path].get(label).get(parameter["item"])
    if placeholder == "main_var":
        return variable
    elif placeholder == "main_var_flag":
        return get_flag_var(variable, variables.split(","))
    return placeholder


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
    Output("figure-menu-label-spinner", "data"),
    Input("figure-type-selector", "value"),
    Input("variable", "value"),
)
def get_label(label, variable):
    if variable is None:
        return None, None
    logger.debug("Selected figure type preset: %s", label)
    return label, None


@callback(
    Output("figure-type-selector", "options"),
    Output("figure-type-selector", "value"),
    Input("location", "pathname"),
)
def get_plot_types(path):
    if path == "/":
        return None, None
    location_items = path.split("/")
    presets = {
        item.lower().replace(" ", "_").replace("-", ""): {"label": item, "value": item}
        for item in figure_presets.get(location_items[1], {}).keys()
    }
    default_figure = list(presets.values())[0]["value"]
    location_preset = (
        presets.get(location_items[3]) if len(location_items) > 3 else None
    )

    return (
        list(presets.values()),
        location_preset["value"] if location_preset else default_figure,
    )
