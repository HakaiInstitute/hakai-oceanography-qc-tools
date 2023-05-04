import logging
import os
import shutil
from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Dash, Input, Output, State, callback, ctx, dash_table, dcc, html

from hakai_qc.qc import update_dataframe
from hakai_qc.flags import flag_color_map, get_hakai_variable_flag, flags_conventions
from hakai_qc.nutrients import nutrient_variables, run_nutrient_qc

# from pages.nutrients import get_flag_var
from utils import load_config

config = load_config()
variables_flag_mapping = {"no2_no3_um": "no2_no3_flag"}
nutrient_variables_flags = [get_hakai_variable_flag(var) for var in nutrient_variables]
quality_levels = [
    "Raw",
    "Technician",
    "Technicianm",
    "Technicianr",
    "Technicianmr",
    "Principal Investigator",
]
MODULE_PATH = os.path.dirname(__file__)


def get_flag_var(var):
    return variables_flag_mapping.get(var, var + "_flag")


logger = logging.getLogger(__name__)
selection_table = dash_table.DataTable(
    id="selected-data-table",
    page_size=40,
    sort_action="native",
    row_deletable=True,
    style_header={
        "fontWeight": "bold",
        "fontSize": "14px",
        "backgroundColor": config["NAVBAR_COLOR"],
        "color": "white",
        "textAlign": "center",
    },
    style_cell={
        # all three widths are needed
        "maxWidth": 250,
        "minWidth": 100,
        "textAlign": "center",
        "fontSize": "12px",
    },
    style_data={"whiteSpace": "normal", "height": "auto", "lineHeight": "15px"},
    style_cell_conditional=[
        {
            "if": {"column_id": "hakai_id"},
            "textAlign": "left",
            "backgroundColor": config["NAVBAR_COLOR"],
            "color": "white",
        },
        {
            "if": {"column_id": "comments"},
            "textAlign": "left",
            "color": "#B52026",
        },
    ],
    style_table={
        "maxWidth": "100%",
        "float": "center",
        "overflowX": "auto",
    },
)
selection_interface = dbc.Collapse(
    [
        dbc.Form(
            dbc.Row(
                [
                    dbc.Label("Apply", width="auto"),
                    dbc.Col(
                        dcc.Dropdown(
                            options=[
                                "Flag",
                                "Quality Level",
                                "Automated QC",
                            ],
                            value="Flag",
                            id="selection-action",
                            clearable=False,
                            className="selection-action",
                        ),
                    ),
                    dbc.Label("=", width="auto"),
                    dbc.Col(
                        dcc.Dropdown(
                            id="selection-apply",
                            clearable=False,
                            className="selection-apply",
                        ),
                    ),
                    dbc.Label("to all", width="auto"),
                    dbc.Col(
                        dcc.Dropdown(
                            id="selection-to", clearable=False, className="selection-to"
                        ),
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Apply",
                            id="selection-apply-button",
                            color="primary",
                        ),
                        width="auto",
                    ),
                ],
                className="g-2 selection-area",
            )
        ),
        dbc.Button(
            html.Div(
                [
                    "Download .xlsx",
                    dbc.Spinner(
                        html.Div(id="hakai-excel-load-spinner"),
                        size="lg",
                    ),
                ]
            ),
            id="download-qc-excel-button",
        ),
        dcc.Download(id="download-qc-excel"),
        selection_table,
    ],
    is_open=True,
    id="selection-interface",
)


@callback(
    Output("selection-apply", "options"),
    Output("selection-apply", "value"),
    Output("selection-to", "value"),
    Output("selection-to", "options"),
    Input("selection-action", "value"),
    Input({"type": "graph", "page": ALL}, "selectedData"),
)
def set_selection_apply_options(action, dataSelected):
    no_selection = not bool([selected for selected in dataSelected if selected])
    apply_to = [
        {
            "label": "Selection",
            "value": "selection",
            "disabled": no_selection,
        },
    ]
    if action == "Flag":
        apply_to += [{"label": "Unknown", "value": "UKN"}]
        return (
            ["AV", "SVC", "SVD"],
            "AV",
            "UKN" if no_selection else "selection",
            apply_to,
        )
    elif action == "Quality Level":
        apply_to += [{"label": ql, "value": ql} for ql in quality_levels]
        return quality_levels, quality_levels[0], "raw", apply_to
    else:
        apply_to += [
            {"label": "Unknown", "value": "UKN"},
            {"label": "All", "value": "all"},
        ]
        return [], None, "UKN" if no_selection else "selection", apply_to


@callback(
    dict(
        data=Output("selected-data-table", "data"),
        columns=Output("selected-data-table", "columns"),
        dropdown=Output("selected-data-table", "dropdown"),
        hidden_columns=Output("selected-data-table", "hidden_columns"),
        style_data_conditional=Output("selected-data-table", "style_data_conditional"),
    ),
    inputs=[
        State("selected-data-table", "data"),
        [
            Input({"id": "selected-data", "source": "figure"}, "data"),
            Input({"id": "selected-data", "source": "auto-qc"}, "data"),
            Input({"id": "selected-data", "source": "flags"}, "data"),
        ],
    ],
)
def update_selected_data(selected_data, newly_selected):
    logger.debug(
        "updated selection data: selected=%s, newly_selected=%s",
        selected_data,
        newly_selected,
    )
    newly_selected = [
        pd.DataFrame(source)
        for source in newly_selected
        if source is not None and len(source) > 0
    ]
    if not selected_data and not newly_selected:
        logger.debug("no selection exist")
        return {
            "data": None,
            "columns": None,
            "dropdown": None,
            "hidden_columns": None,
            "style_data_conditional": None,
        }
    if not selected_data:
        logger.debug("add a new selection to an empty list %s", newly_selected)
        return generate_qc_table_style(pd.concat(newly_selected))

    df = pd.DataFrame(selected_data)
    # logger.debug("append to a selection %s",df)
    logger.debug("new selection %s", newly_selected)
    for source in reversed(newly_selected):
        df_newly_selected = pd.DataFrame(source)
        logger.debug("append selection source %s", source)
        df = update_dataframe(df, df_newly_selected, on=["hakai_id"], how="outer")

    return generate_qc_table_style(df)


def generate_qc_table_style(data):
    if data.empty:
        return {
            "data": None,
            "columns": None,
            "dropdown": None,
            "hidden_columns": None,
            "style_data_conditional": None,
        }
    columns = [
        {
            "name": i,
            "id": i,
            "selectable": i.endswith("_flag"),
            "editable": i.endswith("_flag"),
            "hideable": i != "hakai_id",
            "presentation": "dropdown" if i.endswith("_flag") else None,
        }
        for i in data.columns
    ] + [dict(name="id", id="id")]
    flag_columns = [col for col in data.columns if col.endswith("_flag")]
    logger.debug("QC columns: %s", columns)
    logger.debug("Flag columns: %s", flag_columns)
    color_conditional = (
        {
            "if": {"column_id": col, "filter_query": "{%s} = '%s'" % (col, flag)},
            "backgroundColor": flag_color,
            "color": "white",
        }
        for col in flag_columns
        for flag, flag_color in flag_color_map.items()
    )
    blank_conditional = (
        {
            "if": {"column_id": col, "filter_query": "{%s} = ''" % col},
            "backgroundColor": "light_grey",
            "color": "black",
        }
        for col in flag_columns
    )
    selection_conditional = [
        {
            "if": {"state": "active"},
            "fontWeight": "bold",
            "border": "2px solid black",
        }
    ]
    dropdown_menus = {
        col: {"options": flags_conventions["Hakai"]} for col in flag_columns
    }
    logger.debug("Dropdown menus: %s", dropdown_menus)
    return dict(
        data=data.assign(id=data["hakai_id"]).to_dict("records"),
        columns=columns,
        dropdown=dropdown_menus,
        hidden_columns=[
            "action",
            "date",
            "target_depth_m",
            "start_depth",
            "bottom_depth",
            "latitude",
            "longitude",
            "bottle_drop",
            "drop",
            "survey",
            "work_area",
            "site_id",
            "descent_rate_flag",
            "density_flag",
            "absolute_salinity_flag",
            "conservative_temperature_flag",
            "sos_un_flag",
            "spec_cond_flag",
            "depth_flag",
            "pressure_flag",
            "id",
        ],
        style_data_conditional=(
            *color_conditional,
            *blank_conditional,
            *selection_conditional,
        ),
    )


def get_selected_records_from_graph(graph_selected, custom_data_variables):
    available_selection = [graph for graph in graph_selected if graph]
    if not available_selection:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            point["customdata"][: len(custom_data_variables)]
            for graph in available_selection
            for point in graph["points"]
        ],
        columns=custom_data_variables,
    )


@callback(
    Output({"id": "selected-data", "source": "figure"}, "data"),
    Output({"id": "selected-data", "source": "auto-qc"}, "data"),
    Input("selection-apply-button", "n_clicks"),
    State("selection-action", "value"),
    State("selection-apply", "value"),
    State("selection-to", "value"),
    State({"type": "graph", "page": ALL}, "selectedData"),
    State("variable", "value"),
    State("dataframe", "data"),
    State({"id": "selected-data", "source": "figure"}, "data"),
    State({"id": "selected-data", "source": "auto-qc"}, "data"),
    State({"id": "selected-data", "source": "flags"}, "data"),
)
def apply_to_selection(
    apply,
    action,
    apply_value,
    to,
    graph_selections,
    variable,
    data,
    manually_selected_data,
    auto_qced_data,
    flag_data,
):
    def _add_flag_selection(df_new, df_previous):
        logger.debug(
            "Update len(%s)\n%s \n\n len(%s)\n%s",
            len(df_new) if df_new is not None else None,
            df_new,
            len(df_previous) if df_previous is not None else None,
            df_previous,
        )
        if df_previous is not None:
            return update_dataframe(df_previous, df_new, on=on)
        elif df_new is None or df_new.empty:
            return df_previous
        return df_new

    def _return_json(df):
        return None if df is None else df.reset_index().to_dict("records")

    on = ["hakai_id"]
    if not variable:
        return auto_qced_data, manually_selected_data

    flag_var = get_flag_var(variable) if action == "Flag" else "quality_level"

    # Get record list selected
    graph_selected = get_selected_records_from_graph(graph_selections, ["hakai_id"])
    if graph_selected.empty and to == "selection":
        logger.debug("no selection")
        return manually_selected_data, auto_qced_data
    elif not graph_selected.empty:
        graph_selected = graph_selected.groupby(on).first()
    logger.debug("Data selected = %s", len(graph_selected))

    # Update data with already selected data
    data = pd.DataFrame(data).groupby(["hakai_id"]).first()
    manually_selected_data = (
        pd.DataFrame(manually_selected_data).groupby(["hakai_id"]).first()
        if manually_selected_data
        else None
    )
    auto_qced_data = (
        pd.DataFrame(auto_qced_data).groupby(["hakai_id"]).first()
        if auto_qced_data
        else None
    )
    flag_data = (
        pd.DataFrame(flag_data).groupby(["hakai_id"]).first() if flag_data else None
    )

    if flag_data is not None:
        data = update_dataframe(data, flag_data, on=["hakai_id"])
    if manually_selected_data is not None:
        data = update_dataframe(data, manually_selected_data, on=["hakai_id"])
    if auto_qced_data is not None:
        data = update_dataframe(data, auto_qced_data, on=["hakai_id"])

    # Apply action
    logger.debug("Apply %s to data[%s=='%s'] = %s", action, flag_var, to, apply_value)
    if action in ("Flag", "Quality Level") and to == "selection":
        logger.debug("Apply '%s'=%s to selection", action, apply_value)
        manually_selected_data = _add_flag_selection(
            graph_selected.assign(**{flag_var: apply_value}),
            manually_selected_data,
        )
    elif action in ("Flag", "Quality Level"):
        filter_by = f"{flag_var} == '{to}'" if to != "UKN" else f"{flag_var}.isna()"
        logger.debug(
            "Filter data by %s and apply %s=%s", filter_by, flag_var, apply_value
        )

        selected_data = data.query(filter_by if flag_var in data else None).assign(
            **{flag_var: apply_value}
        )
        if not selected_data.empty:
            manually_selected_data = _add_flag_selection(
                selected_data[flag_var], manually_selected_data
            )
        else:
            logger.debug("Filter returned no data")

    elif action == "Automated QC":
        logger.debug("Run Automated QC")
        data = data.dropna(subset=nutrient_variables).reset_index()
        data["collected"] = pd.to_datetime(data["collected"], utc=True).dt.tz_localize(
            None
        )
        auto_qced_data = run_nutrient_qc(data, overwrite_existing_flags=True)
        # Standardize flag tables
        auto_qced_data = (
            auto_qced_data[["hakai_id"] + nutrient_variables_flags]
            .groupby("hakai_id")
            .first()
        )
        data = data[["hakai_id"] + nutrient_variables_flags].groupby("hakai_id").first()

        # Compare prior and after qc results
        df_compare = auto_qced_data.compare(data).swaplevel(axis="columns")
        if to == "selection":
            logger.debug("Apply qc to selection: %s", graph_selected.index.values)
            auto_qced_data = df_compare["self"].query(
                "hakai_id in @graph_selected.index.values"
            )[nutrient_variables_flags]
            logger.debug("Qc update %s records", len(auto_qced_data))
        elif to == "UKN":
            logger.debug("Apply qc to unknown %s", nutrient_variables_flags)
            auto_qced_data = df_compare.loc[
                df_compare["other"][nutrient_variables_flags].isna().all(axis="columns")
            ]["self"][nutrient_variables_flags]
            logger.debug("Qc update %s records", len(auto_qced_data))
        elif to == "all":
            logger.debug("Apply ")
            auto_qced_data = df_compare["self"][nutrient_variables_flags]

    return _return_json(manually_selected_data), _return_json(auto_qced_data)


@callback(
    Output("download-qc-excel", "data"),
    Output("hakai-excel-load-spinner", "children"),
    Input("download-qc-excel-button", "n_clicks"),
    State("selected-data-table", "data"),
    State("location", "pathname"),
)
def get_qc_excel(n_clicks, data, location):
    """Save file to an excel file format compatible with the Hakai Portal upload"""
    if data is None:
        return None, None
    logger.info("Generate excel file")
    df = pd.DataFrame(data).drop(
        columns=["id", "start_depth", "target_depth_m", "bottle_drop", "collected"],
        errors="ignore",
    )
    temp_file = os.path.join(
        config["TEMP_FOLDER"],
        f"hakai-qc-{location[1:]}-{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}.xlsx",
    )
    logger.debug("Make a copy from the %s template", location[1:])
    shutil.copy(
        os.path.join(
            MODULE_PATH, f"../assets/hakai-template-{location[1:]}-samples.xlsx"
        ),
        temp_file,
    )
    logger.debug("Add data to qc excel file")
    with pd.ExcelWriter(
        temp_file, engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        df.to_excel(writer, sheet_name="Hakai Data", index=False)
    logger.info("Upload Hakai QC excel file")
    return dcc.send_file(temp_file), None
