import pandas as pd
import gsw


def _get_qc_flag_per_variable():
    pass


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
        df["absolute_salinity"], df["converstive_temperature"], df["pressure"]
    )
    df["sigma0"] = gsw.sigma0(df["absolute_salinity"], df["convervative_temperature"])

    return df


def generate_qc_flags(data: pd.DataFrame, variable: str) -> pd.DataFrame:
    qartod_flag = f"{variable}_flag_level_1"
    hakai_flag = f"{variable}_flag"

    qc_flags = data.groupby("hakai_id").agg({qartod_flag: "median", hakai_flag: set})
