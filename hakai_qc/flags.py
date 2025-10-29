# Flag convention
flag_color_map = {
    "AV": "#2ECC40",
    "SVC": "#FF851B",
    "SVD": "#FF4136",
    "MV": "#FFDC00",
    "BDL": "pink",
    "NA": "purple",
    1: "#2ECC40",
    3: "#FF851B",
    4: "#FF4136",
    9: "#FFDC00",
    "1": "#2ECC40",
    "3": "#FF851B",
    "4": "#FF4136",
    "9": "#FFDC00",
}
flag_qartod_to_hakai = {
    1: "AV",
    2: "",
    3: "SVC",
    4: "SVD",
    9: "NA",
}
flags_conventions = {
    "Hakai": [
        {"label": "Acceptable Value", "value": "AV"},
        {"label": "Suspicious Value Cautious", "value": "SVC"},
        {"label": "Suspicious Value Discard", "value": "SVD"},
        {"label": "Below Detection Limit", "value": "BDL"},
    ],
    "QARTOD": [
        {"label": "GOOD", "value": 1},
        {"label": "UNKNOWN", "value": 2},
        {"label": "SUSPECT", "value": 3},
        {"label": "FAIL", "value": 4},
        {"label": "MISSING", "value": 9},
    ],
    "quality_level": [
        {"label": "Raw", "value": "Raw"},
        {"label": "Technicianm", "value": "Technicianm"},
        {"label": "Technicianr", "value": "Technicianr"},
        {"label": "Technicianmr", "value": "Technicianmr"},
        {"label": "Principal Investigator", "value": "Principal Investigator"},
    ],
    "row_flag": [
        {"label": "Collected", "value": "Collected"},
        {"label": "Submitted", "value": "Submitted"},
        {"label": "Results", "value": "Results"},
        {"label": "Not Available", "value": "Not Available"},
    ],
}
flag_tooltips = {
    "Hakai": """
    Acceptable Value = AV 
    Suspicious Value Cautious = SVC
    Suspicious Value Discard = SVD
    Below Detection Limit = BDL
    Not Available = NA
    """,
    "quality_level": """
    - Raw = collected but no event QC / nothing has been done yet.
    - Technicianm = metadata Rechecked & moved post-survey
    - Technicianmr = Metadata QC and Results back from the lab matched with metadata
    - Technicianr = Results are back from the lab but metadata hasn’t been QC’d
    - Principal Investigator = paper / data product ready Data has gone through QC
    """,
}

flag_mapping = {"no2_no3_um": "no2_no3_flag"}


def get_hakai_variable_flag(variable):
    return flag_mapping.get(variable, f"{variable}_flag")
