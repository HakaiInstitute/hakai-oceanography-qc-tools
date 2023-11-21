import gsw
import pandas as pd

from hakai_qc.flags import flag_qartod_to_hakai


def get_derive_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Generate ctd derived variables

    Args:
        df (pd.DataFrame): Hakai CTD data dataframe

    Returns:
        pd.DataFrame: Same initial dataframe with
            the including derived variables.
    """

    df["absolute_salinity"] = gsw.SA_from_SP(
        df["salinity"],
        df["pressure"],
        df["longitude"].fillna(df["station_longitude"]),
        df["latitude"].fillna(df["station_latitude"]),
    )
    df["conservative_temperature"] = gsw.CT_from_t(
        df["absolute_salinity"], df["temperature"], df["pressure"]
    )
    df["density"] = gsw.rho(
        df["absolute_salinity"], df["conservative_temperature"], df["pressure"]
    )
    df["sigma0"] = gsw.sigma0(df["absolute_salinity"], df["conservative_temperature"])

    return df


def generate_qc_flags(data: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Review the automatically generated flags and assign a cast global flag.

    Args:
        data (pd.DataFrame): Cast data
        variable (str): Column to review

    Returns:
        pd.DataFrame: hakai_id specific flag dataframe
    """

    def _common_automated_qc_flag(flags):
        return flags.dropna().median()

    def _review_hakai_flag(flags):
        flag, comment = None, []

        if flags.str.contains("bottom_hit_test").any():
            comment += ["Instrument seems to have hit bottom."]
        if 0 < len(flags.loc[flags.astype(str).str.contains("density_inversion")]) <= 4:
            comment += ["Some density inversion are present."]
        if 4 < len(flags.loc[flags.astype(str).str.contains("density_inversion")]):
            comment += ["A significant number of density inversion are present."]
            flag = "SVC"
        return {hakai_flag: flag, "comments": "\n".join(comment)}

    qartod_flag = f"{variable}_flag_level_1"
    hakai_flag = f"{variable}_flag"

    qc_flags = data.groupby("hakai_id").agg(
        {qartod_flag: _common_automated_qc_flag, hakai_flag: _review_hakai_flag}
    )
    suggested_flags = qc_flags[hakai_flag].apply(pd.Series)
    suggested_flags[hakai_flag] = suggested_flags[hakai_flag].fillna(
        qc_flags[qartod_flag].replace(flag_qartod_to_hakai)
    )

    return suggested_flags
