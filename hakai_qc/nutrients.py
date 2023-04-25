from hakai_qc.flags import flag_qartod_to_hakai, get_hakai_variable_flag
from hakai_qc.qc import qartod_compare, qc_dataframe

variables_flag_mapping = {"no2_no3_um": "no2_no3_flag"}
nutrient_variables = ["no2_no3_um", "sio2", "po4"]
nutrients_qc_configs = {
    "-5 < line_out_depth < 50": """
        contexts:
                -   window:
                        starting: 2010-01-01T00:00:00Z
                        ending: null
                    streams:
                        no2_no3_um:
                            qartod:
                                gross_range_test:
                                    suspect_span: [0, 36]
                                    fail_span: [0, 40]
                        po4:
                            qartod:
                                gross_range_test:
                                    suspect_span: [0, 3]
                                    fail_span: [0, 4]
                        sio2:
                            qartod:
                                gross_range_test:
                                    suspect_span: [0,80]
                                    fail_span: [0,100]
        """,
    "50<=line_out_depth": """
        contexts:
             -  window:
                    starting: 2010-01-01T00:00:00Z
                    ending: null
                streams:
                    no2_no3_um:
                        qartod:
                            gross_range_test:
                                suspect_span: [0, 36]
                                fail_span: [0, 40]
                            spike_test:
                                suspect_threshold: 2
                                fail_threshold: 3
                                method: 'differential'
                    po4:
                        qartod:
                            gross_range_test:
                                suspect_span: [0, 3]
                                fail_span: [0, 4]
                            spike_test:
                                suspect_threshold: 0.2
                                fail_threshold: 0.4
                                method: 'differential'
                    sio2:
                        qartod:
                            gross_range_test:
                                suspect_span: [0,80]
                                fail_span: [0,100]
                            spike_test:
                                suspect_threshold: 8
                                fail_threshold: 12
                                method: 'differential'
        """,
}
nutrients_qc_bdl = {
    "no2_no3_um": 0.036,
    "po4": 0.032,
    "sio2": 0.1,
}


def run_nutrient_qc(
    df,
    config=None,
    groupby=["site_id", "line_out_depth"],
    overwrite_existing_flags=False,
):
    if config is None:
        config = nutrients_qc_configs
    """Run Hakai Nutrient automated QC"""
    # Run QARTOD tests
    original_columns = df.columns
    df = df.sort_values(["site_id", "line_out_depth", "collected"])
    df = qc_dataframe(
        df,
        configs=config,
        groupby=groupby,
        axes=dict(
            time="collected", z="line_out_depth", lat="latitude", lon="longitude"
        ),
    )

    # aggregate flags
    for var in ["no2_no3_um", "po4", "sio2"]:
        agg_flag = f"{var}_qartod_aggregate"
        df.loc[:, agg_flag] = qartod_compare(
            df.filter(like=f"{var}_qartod_")
            .fillna(9)
            .astype(int)
            .transpose()
            .to_numpy()
        )
        df[agg_flag] = df[agg_flag].replace(flag_qartod_to_hakai)

        # Apply BDL flag
        if var in nutrients_qc_bdl:
            df.loc[df[var] < nutrients_qc_bdl[var], agg_flag] = "BDL"

        # Map to hakai convention and update empty flags
        var_flag = get_hakai_variable_flag(var)
        df.loc[:, var_flag] = (
            df[agg_flag]
            if overwrite_existing_flags
            else df[var_flag].fillna(df[agg_flag])
        )

    return df[original_columns]
