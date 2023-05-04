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
    2: "UKN",
    3: "SVC",
    4: "SVD",
    9: "MV",
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
}

flag_mapping = {"no2_no3_um": "no2_no3_flag"}


def get_hakai_variable_flag(variable):
    return flag_mapping.get(variable, f"{variable}_flag")
