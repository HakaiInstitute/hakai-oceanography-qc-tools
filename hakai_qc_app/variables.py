PRIMARY_VARIABLES = {
    "nutrients": ["sio2", "po4", "no2_no3_um"],
    "ctd": [
        "temperature",
        "salinity",
        "dissolved_oxygen_ml_l",
        "rinko_do_ml_l",
        "dissolved_oxygen_percent",
        "turbidity",
        "flc",
        "par",
        "c_star_at",
    ],
}

VARIABLES_LABEL = {
    "sio2": "SiO2 (uM)",
    "po4": "PO4 (uM)",
    "no2_no3_um": "NO2 NO3 (uM)",
    "line_out_depth": "Bottle Target Depth (m)",
    "collected": "Collection Time",
    "AV": "Accepted Value",
    "UKN": "Unknown",
    "NA": "Not Available",
    "SVC": "Suspicious Value Careful",
    "SVD": "Suspicious Value Discard",
    "BDL": "Below Detection Limit",
    "ctd": "CTD",
    "depth": "Depth (m)",
    "row_flag": "Sample Status",
}

pages = {
    "nutrients": [
        {
            "endpoint": "eims/views/output/nutrients",
            "fields": [
                "work_area",
                "organization",
                "project",
                "survey",
                "date",
                "sampling_bout",
                "site_id",
                "hakai_id",
                "collected",
                "lat",
                "long",
                "gather_lat",
                "gather_long",
                "line_out_depth",
                "pressure_transducer_depth",
                "lab_technician",
                "no2_no3_um",
                "po4",
                "sio2",
                "no2_no3_flag",
                "po4_flag",
                "sio2_flag",
                "row_flag",
                "metadata_qc_flag",
                "quality_level",
                "comments",
                "quality_log",
                "analyzing_lab",
            ],
            "upload_fields": [
                "hakai_id",
                "no2_no3_flag",
                "po4_flag",
                "sio2_flag",
                "row_flag",
                "metadata_qc_flag",
                "quality_level",
                "comments",
                "quality_log",
                "analyzing_lab",
            ],
        }
    ],
    "ctd": [
        {
            "endpoint": "ctd/views/file/cast/data",
            "fields": [
                "hakai_id",
                "station",
                "latitude",
                "longitude",
                "station_longitude",
                "station_latitude",
                "start_dt",
                "direction_flag",
                "depth",
                "pressure",
                "conductivity",
                "conductivity_flag",
                "conductivity_flag_level_1",
                "temperature",
                "temperature_flag",
                "temperature_flag_level_1",
                "salinity",
                "salinity_flag",
                "salinity_flag_level_1",
                "dissolved_oxygen_ml_l",
                "dissolved_oxygen_ml_l_flag",
                "dissolved_oxygen_ml_l_flag_level_1",
                "rinko_do_ml_l",
                "rinko_do_ml_l_flag",
                "rinko_do_ml_l_flag_level_1",
                "dissolved_oxygen_percent",
                "dissolved_oxygen_percent_flag",
                "dissolved_oxygen_percent_flag_level_1",
                "par",
                "par_flag",
                "par_flag_level_1",
                "flc",
                "flc_flag",
                "flc_flag_level_1",
                "turbidity",
                "turbidity_flag",
                "turbidity_flag_level_1",
                "c_star_at",
                "c_star_at_flag",
                "c_star_at_flag_level_1",
            ],
        },
        {
            "endpoint": "eims/views/output/ctd_qc",
            "fields": [
                "hakai_id",
                "collected",
                "work_area",
                "survey",
                "site_id",
                "depth_flag",
                "pressure_flag",
                "conductivity_flag",
                "salinity_flag",
                "temperature_flag",
                "dissolved_oxygen_ml_l_flag",
                "dissolved_oxygen_percent_flag",
                "rinko_do_ml_l_flag",
                "par_flag",
                "flc_flag",
                "turbidity_flag",
                "c_star_at_flag",
                "comments",
            ],
        },
    ],
}
DEFAULT_HIDDEN_COLUMNS_IN_TABLE = [
    "action",
    "sampling_bout",
    "project_specific_id",
    "source",
    "collection_method",
    "preserved",
    "analyzed",
    "no2_no3_um",
    "no2_no3_ugl",
    "po4",
    "sio2",
    "rn",
    "lat",
    "long",
    "gather_lat",
    "gather_long",
    "filtered",
    "filter_type",
    "volume",
    "installed",
    "nh4_",
    "tp",
    "tdp",
    "tn",
    "tdn",
    "no2_no3_units",
    "nh4__flag",
    "srp",
    "po4filt",
    "no3filt",
    "po4punfl",
    "po4pfilt",
    "no3nfilt",
    "no3nunfl",
    "nh4nunfl",
    "nh4_flag",
    "tp_flag",
    "tdp_flag",
    "tn_flag",
    "tdn_flag",
    "srp_flag",
    "po4filt_flag",
    "po4pfilt_flag",
    "no3filt_flag",
    "no3pfilt_flag",
    "po4punfl_flag",
    "no3nunfl_flag",
    "nh4nunfl_flag",
    "analyzing_lab",
    "event_pk",
    "rn",
    "is_replicate",
    "organization",
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
    "depth",
]
