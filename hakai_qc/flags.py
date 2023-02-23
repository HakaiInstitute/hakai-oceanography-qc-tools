# Flag convention
flag_color_map = {
    "AV": "#2ECC40",
    "SVC": "#FF851B",
    "SVD": "#FF4136",
    "MV": "#FFDC00",
    "BDL": "pink",
}
flag_qartod_to_hakai = {
    1: "AV",
    2: "UKN",
    3: "SVC",
    4: "SVD",
    9: "MV",
}

flag_mapping = {"no2_no3_um": "no2_no3_flag"}


def get_hakai_variable_flag(variable):
    return flag_mapping.get(variable, f"{variable}_flag")
