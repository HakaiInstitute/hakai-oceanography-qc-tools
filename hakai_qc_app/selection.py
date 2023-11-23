import math
import re
import shutil
from datetime import datetime
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Input, Output, State, callback, ctx, dash_table, dcc, html
from loguru import logger

from hakai_qc.ctd import generate_qc_flags
from hakai_qc.flags import (
    flag_color_map,
    flag_tooltips,
    flags_conventions,
    get_hakai_variable_flag,
)
from hakai_qc.nutrients import nutrient_variables, run_nutrient_qc
from hakai_qc.qc import update_dataframe
from hakai_qc_app.variables import (
    DEFAULT_HIDDEN_COLUMNS_IN_TABLE,
    VARIABLES_LABEL,
    pages,
)

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
sample_status = ["Collected", "Submitted", "Results", "Not Available"]
MODULE_PATH = Path(__file__).parent


def get_flag_var(var):
    return variables_flag_mapping.get(var, var + "_flag")


selection_table = dash_table.DataTable(
    id="qc-table",
    page_size=40,
    sort_action="native",
    filter_action="native",
    row_selectable="multi",
    sort_mode="multi",
    style_header={
        "fontWeight": "bold",
        "fontSize": "14px",
        "backgroundColor": "#B52026",
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
            "backgroundColor": "#B52026",
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
selection_interface = dbc.Row(
    [
        dbc.Label("To all", width="auto"),
        dbc.Col(
            dcc.Dropdown(
                id="selection-to",
                clearable=False,
                className="selection-to",
            ),
        ),
        dbc.Label(", apply", width="auto"),
        dbc.Col(
            dcc.Dropdown(
                options=[
                    "Flag",
                    "Quality Level",
                    "Sample Status",
                    "Automated QC",
                ],
                value="Flag",
                id="selection-action",
                clearable=False,
                className="selection-action",
                persistence=True,
                persistence_type="session",
            ),
        ),
        dbc.Label("=", width="auto"),
        dbc.Col(
            dcc.Dropdown(
                id="selection-apply",
                clearable=False,
                className="selection-apply",
                persistence=True,
                persistence_type="session",
            ),
        ),
        dbc.Tooltip(
            id="selection-apply-tooltip",
            target="selection-apply",
            style={"width": "300px"},
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

table_extra_buttons = html.Div(
    [
        dbc.ButtonGroup(
            [
                dbc.Button(
                    html.Div(
                        [
                            "Download",
                            dbc.Spinner(
                                html.Div(id="hakai-excel-load-spinner"),
                                size="lg",
                            ),
                        ]
                    ),
                    id="download-qc-excel-button",
                ),
                dbc.Button(
                    html.Div(
                        [
                            "Upload",
                            dbc.Spinner(
                                html.Div(id="hakai-upload-to-hakai-spinner"),
                                size="lg",
                            ),
                        ]
                    ),
                    id="upload-to-hakai-button",
                    disabled=True,
                ),
            ],
            className="me-1",
        ),
        dbc.ButtonGroup(
            [
                dbc.Button(
                    "Clear",
                    id="clear-selected-row-table",
                ),
                dbc.Button(
                    "Update",
                    id="update-qc-table",
                ),
            ],
            className="me-1",
        ),
    ],
    className="qc-table-extra-buttons",
)

qc_section = dbc.Collapse(
    [
        dbc.Row(
            [table_extra_buttons, selection_interface],
            justify="between",
            align="center",
            className="qc-menu",
        ),
        dcc.Download(id="download-qc-excel"),
        dbc.Progress(id="flag-progress-bar", className="flag-progress-bar"),
        selection_table,
    ],
    is_open=True,
    id="selection-interface",
)


@callback(
    Output("qc-table", "active_cell"),
    Output("qc-table", "page_current"),
    Input(
        {"type": "graph", "page": ALL},
        "clickData",
    ),
    State("qc-table", "derived_virtual_data"),
    State("qc-table", "hidden_columns"),
    State("qc-table", "active_cell"),
    State("variable", "value"),
    State("qc-table", "page_current"),
    State("qc-table", "page_size"),
    State("qc-table", "selected_cells"),
)
def select_qc_table(
    clicked,
    qc_data,
    hidden_qc_columns,
    active_cell,
    column,
    current_page,
    page_size,
    selected_cells,
):
    if (
        not clicked
        or clicked[0] is None
        or clicked[0]["points"][0].get("customdata") is None
    ):
        return active_cell, current_page
    logger.debug("clicked={}", clicked)
    logger.debug("selected_cells={}", selected_cells)
    selected_hakai_id = clicked[0]["points"][0]["customdata"][0]
    selected_row = [
        id for id, row in enumerate(qc_data) if row["hakai_id"] == selected_hakai_id
    ][0]
    current_page = math.floor(selected_row / page_size)
    selected_col = {
        col: id
        for id, col in enumerate(
            col for col in qc_data[0].keys() if col not in hidden_qc_columns
        )
    }[get_hakai_variable_flag(column)]
    active_cell = {
        "row": selected_row - current_page * page_size,
        "column": selected_col,
        "column_id": column,
        "row_id": selected_hakai_id,
    }
    logger.debug("Select cell in qc-table from figure click {}", active_cell)
    return active_cell, current_page


@callback(
    Output({"type": "dataframe-subset", "subset": "query"}, "value"),
    Output("clear-selected-row-table", "disabled"),
    Input("qc-table", "selected_row_ids"),
)
def filter_by_selected_rows(selected_rows_ids):
    if not selected_rows_ids:
        return None, True
    return f"hakai_id in {selected_rows_ids}", False


@callback(
    Output("qc-table", "selected_rows"),
    Output("qc-table", "selected_row_ids"),
    Input("clear-selected-row-table", "n_clicks"),
)
def clear_selection(n_click):
    return [], []


@callback(
    Output("selection-apply", "options"),
    Output("selection-apply", "value"),
    Output("selection-apply-tooltip", "children"),
    Output("selection-to", "value"),
    Output("selection-to", "options"),
    Input("selection-action", "value"),
    Input({"type": "graph", "page": ALL}, "selectedData"),
    State("selection-apply", "value"),
    State("selection-to", "value"),
)
def set_selection_apply_options(action, dataSelected, apply, to):
    def _get_values(items):
        return [item["value"] for item in items]

    no_selection = not bool([selected for selected in dataSelected if selected])
    apply_to_options = [
        {
            "label": "Selection",
            "value": "selection",
            "disabled": no_selection,
        },
    ]
    if action == "Flag":
        apply_to_options += [
            {"label": "Unknown", "value": "unknown"},
            {"label": "All", "value": "all"},
        ]
        return (
            flags_conventions["Hakai"],
            apply if apply in _get_values(flags_conventions["Hakai"]) else "AV",
            flag_tooltips["Hakai"],
            to or "UKN" if no_selection else "selection",
            apply_to_options,
        )
    elif action == "Sample Status":
        apply_to_options += [{"label": ql, "value": ql} for ql in sample_status]
        return (
            sample_status,
            apply if apply in sample_status else "Results",
            None,
            "Not Available" if no_selection else "selection",
            apply_to_options,
        )
    elif action == "Quality Level":
        apply_to_options += [{"label": ql, "value": ql} for ql in quality_levels]
        return (
            quality_levels,
            apply if apply in quality_levels else "Principal Investigator",
            flag_tooltips["quality_level"],
            "Technicianm" if no_selection else "selection",
            apply_to_options,
        )
    else:
        apply_to_options += [
            {"label": "Unknown", "value": "UKN"},
            {"label": "All", "value": "all"},
        ]
        return [], None, None, "UKN" if no_selection else "selection", apply_to_options


@callback(
    dict(
        data=Output("qc-table", "data"),
        columns=Output("qc-table", "columns"),
        dropdown=Output("qc-table", "dropdown"),
        hidden_columns=Output("qc-table", "hidden_columns"),
        style_data_conditional=Output("qc-table", "style_data_conditional"),
    ),
    State("qc-table", "data"),
    Input("qc-source-data", "data"),
    Input("qc-update-data", "data"),
    Input("update-qc-table", "n_clicks"),
)
def update_selected_data(qc_table_data, original_flags, updated_data, update_click):
    if not qc_table_data and not original_flags:
        logger.debug("no qc data available")
        return {
            "data": None,
            "columns": None,
            "dropdown": None,
            "hidden_columns": None,
            "style_data_conditional": None,
        }

    logger.debug(
        "Update qc table with qc_table_data={} updated_data={} original_flags= {}",
        qc_table_data,
        updated_data,
        original_flags,
    )

    if qc_table_data is None and updated_data is None and original_flags:
        original_flags = pd.DataFrame(original_flags)
        original_flags["modified"] = False
        logger.debug("add original flags to the qc table {}", original_flags.columns)
        return generate_qc_table_style(original_flags)

    # Convert data to dataframes
    original_flags = pd.DataFrame(original_flags)
    qc_table_data = pd.DataFrame(qc_table_data)
    updated_data = pd.DataFrame(updated_data)

    logger.debug(
        "Update already existing qc_table[{}]={} with {}",
        len(qc_table_data),
        qc_table_data.columns,
        updated_data.columns,
    )

    # Update table form selection interface
    if ctx.triggered_id == "update-qc-table":
        df = qc_table_data
    else:
        df = update_dataframe(
            qc_table_data,
            updated_data,
            on=["hakai_id"],
            how="outer",
        )

    # Find modified rows
    df["modified"] = (
        ~df[[col for col in df if col in original_flags]]
        .compare(original_flags, keep_shape=True)
        .isna()
        .all(axis=1)
    ).astype(str)
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
    editable_columns = ("comments", "quality_level", "row_flag", "quality_log")
    dropdown_columns = ("quality_level", "row_flag")
    columns = [
        {
            "name": VARIABLES_LABEL.get(i, i),
            "id": i,
            "selectable": i.endswith("_flag") or i in editable_columns,
            "editable": i.endswith("_flag") or i in editable_columns,
            "hideable": i != "hakai_id",
            "presentation": "dropdown"
            if i.endswith("_flag") or i in dropdown_columns
            else None,
        }
        for i in data.columns
    ] + [dict(name="id", id="id")]
    flag_columns = [col for col in data.columns if col.endswith("_flag")]
    logger.debug("QC columns: {}", columns)
    logger.debug("Flag columns: {}", flag_columns)
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
        },
        {
            "if": {
                "column_editable": False,
                "column_id": [col for col in data if col != "hakai_id"],
            },
            "color": "grey",
        },
        {
            "if": {
                "filter_query": "{modified} = True",
            },
            "font-style": "italic",
            "border": "1px solid black",
        },
        {
            "if": {"filter_query": "{modified} = True", "column_id": "modified"},
            "fontWeight": "bold",
        },
    ]
    dropdown_menus = {
        **{col: {"options": flags_conventions["Hakai"]} for col in flag_columns},
        **{
            col: {"options": flags_conventions[col]}
            for col in ["quality_level", "row_flag"]
            if col in data
        },
    }

    logger.debug("Dropdown menus: {}", dropdown_menus)
    return dict(
        data=data.assign(id=data["hakai_id"]).to_dict("records"),
        columns=columns,
        dropdown=dropdown_menus,
        hidden_columns=DEFAULT_HIDDEN_COLUMNS_IN_TABLE,
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
    try:
        return pd.DataFrame(
            [
                point["customdata"][: len(custom_data_variables)]
                for graph in available_selection
                for point in graph["points"]
            ],
            columns=custom_data_variables,
        )
    except KeyError as e:
        logger.error("Failed to retrieve selection: {}", available_selection)
        raise e


@callback(
    Output("selection-apply-button", "disabled"),
    Input("user-initials", "value"),
)
def activate_apply_button(value):
    return not (value and re.fullmatch("[A-Z]+", value))


@callback(
    Output("qc-update-data", "data"),
    Input("selection-apply-button", "n_clicks"),
    State("selection-action", "value"),
    State("selection-apply", "value"),
    State("selection-to", "value"),
    State({"type": "graph", "page": ALL}, "selectedData"),
    State("variable", "value"),
    State("dataframe", "data"),
    State("qc-table", "data"),
    State("location", "pathname"),
    State("user-initials", "value"),
)
def apply_to_selection(
    apply,
    action,
    apply_value,
    to,
    graph_selections,
    variable,
    data,
    qc_data,
    location,
    initials,
):
    def _join_comments(cast):
        if cast["previous_comments"] is None:
            return cast["comments"]
        elif cast["comments"] in cast["previous_comments"]:
            return cast["previous_comments"]
        return f"{cast['previous_comments']}; {cast['comments']}"

    # Ignore empty data
    if not variable or qc_data is None:
        return None
    qc_data = pd.DataFrame(qc_data).groupby(["hakai_id"]).first()

    action_variable = {"Quality Level": "quality_level", "Sample Status": "row_flag"}
    update_variable = action_variable.get(action, get_flag_var(variable))

    # Get list of hakai_id to update
    if to == "selection":
        # Retrieve list of selected hakai_ids from the graph
        logger.debug("List of hakai_ids selected on figure")
        graph_selected = get_selected_records_from_graph(graph_selections, ["hakai_id"])
        if graph_selected.empty:
            logger.debug("no selection")
            return None
        update_hakai_ids = graph_selected["hakai_id"].drop_duplicates().values
    elif to == "unknown":
        query = f'{update_variable}.isna() or {update_variable} in ("UKN")'
        logger.debug("Get hakai_ids with {}", query)
        update_hakai_ids = qc_data.query(query).index.values

    elif to == "all":
        logger.debug("Get the full list of hakai_ids")
        update_hakai_ids = qc_data.index.values
    elif action in ("Quality Level", "Sample Status"):
        if update_variable not in qc_data:
            logger.error("No {} column available", update_variable)
            return qc_data.reset_index().to_dict(orient="records")
        if to == "Not Available":
            query = f"{update_variable}.isna() or {update_variable} == '{to}' "
        else:
            query = f"{update_variable} == '{to}' "
        logger.debug("Update {} => {}", query, apply_value)
        update_hakai_ids = qc_data.query(query).index.values

    else:
        raise RuntimeError(f"Unknown apply action={action} to={to} parameters")

    if not update_hakai_ids.any():
        logger.warning("No records matches action={}, to={}", action, to)
        logger.debug("qc_data={}", qc_data[update_variable].head())
    logger.debug("{} hakai_ids were selected", len(update_hakai_ids))

    # Update data with already selected data
    if action in ("Flag", "Sample Status"):
        logger.debug("Apply {}={} value to the selection", action, apply_value)
        qc_data.loc[update_hakai_ids, update_variable] = apply_value
        return qc_data.reset_index().to_dict(orient="records")
    elif action == "Quality Level":
        logger.debug("Apply qualit_level value to the selection")
        qc_data.loc[update_hakai_ids, update_variable] = apply_value
        if apply_value == "Principal Investigator":
            append_quality_log = f"Data QCd by {initials}"
            quality_log = qc_data.loc[update_hakai_ids, "quality_log"].str.split(
                "\d+\:\s", regex=True
            )
            # find how many lines exists already and since we're using split,
            # the first item is always empty
            n_log = quality_log.apply(len)
            qc_data.loc[update_hakai_ids, "quality_log"] += (
                "\n" + n_log.astype(str) + f": {append_quality_log}"
            )

        return qc_data.reset_index().to_dict(orient="records")
    elif action != "Automated QC":
        logger.error("Unknown method to apply")
        raise RuntimeError(f"unknown action to apply={action}")

    logger.debug("Run Automated QC")
    data = pd.DataFrame(data)
    if "nutrient" in location:
        data = data.dropna(subset=nutrient_variables).reset_index()
        data["collected"] = pd.to_datetime(data["collected"], utc=True).dt.tz_localize(
            None
        )
        auto_qced_data = run_nutrient_qc(data, overwrite_existing_flags=True)
        auto_qced_data = (
            auto_qced_data[["hakai_id"] + nutrient_variables_flags]
            .groupby("hakai_id")
            .first()
        )
        variable_flags = nutrient_variables_flags

    elif "ctd" in location:
        logger.debug(
            "Generate suggested flag for ctd {}: {}", variable, qc_data.columns
        )
        auto_qced_data = generate_qc_flags(data, variable)
        auto_qced_data["previous_comments"] = qc_data["comments"]
        auto_qced_data["comments"] = auto_qced_data.apply(
            _join_comments, axis="columns"
        )
        variable_flags = [f"{variable}_flag", "comments"]

    # Compare prior and after qc results
    qc_data.loc[update_hakai_ids, variable_flags] = auto_qced_data.loc[
        update_hakai_ids, variable_flags
    ]

    return qc_data.reset_index().to_dict(orient="records")


@callback(
    Output("download-qc-excel", "data"),
    Output("hakai-excel-load-spinner", "children"),
    Input("download-qc-excel-button", "n_clicks"),
    State("qc-table", "data"),
    State("location", "pathname"),
)
def get_qc_excel(n_clicks, data, location):
    """Save file to an excel file format compatible with the Hakai Portal upload"""
    if data is None:
        return None, None
    df = pd.DataFrame(data)
    data_type = location.split("/")[1]
    logger.info("Retrieve excel file template for {}", data_type)
    excel_template = MODULE_PATH / f"assets/hakai-template-{data_type}-samples.xlsx"

    variable_output = pages.get(data_type)[0].get("upload_fields")
    logger.debug("Save excel file type:{}", data_type)
    if variable_output:
        logger.debug("Upload only varaibles={}", variable_output)
        df = df[variable_output]
    temp_dir = Path("temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = (
        temp_dir
        / f"hakai-qc-{data_type}-{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}.xlsx"
    )
    logger.info("Copy {} template/update excel file to: {}", data_type, temp_file)
    shutil.copy(
        excel_template,
        temp_file,
    )
    logger.debug("Add data to qc excel file")
    with pd.ExcelWriter(
        temp_file, engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        df.to_excel(writer, sheet_name="Hakai Data", index=False)
    logger.info("Upload Hakai QC excel file")
    return dcc.send_file(temp_file), None


@callback(
    Output("flag-progress-bar", "children"),
    Input("qc-table", "data"),
    Input("variable", "value"),
)
def update_progress_bar(data, variable):
    if data is None:
        return []
    flags = {"green": 50, "warning": 20, "danger": 10.5, "grey": 20}
    flag_variable = get_flag_var(variable)
    df = pd.DataFrame(data)
    if variable in df:
        df = df.query(f"{variable}.notna()")

    flag_column = df[flag_variable].replace(flag_color_map).replace({None: "grey"})
    nrecs = len(flag_column)
    flags = (flag_column.groupby(flag_column).count() / nrecs * 100).to_dict()
    # logger.debug("Flag distribution={}", dist)
    return [
        dbc.Progress(value=value, color=color, bar=True)
        for color, value in flags.items()
    ]
