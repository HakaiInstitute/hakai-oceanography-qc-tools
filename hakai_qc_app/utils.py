import pandas as pd
from hakai_api import Client


def update_dataframe(df, new_df, on=None, suffix="_new", how="outer"):
    """Merge two dataframes on specified columns and update
    missing values from the second dataframe by the first one."""
    # Compbine the two dataframes
    df_merge = pd.merge(df, new_df, how=how, suffixes=("", suffix), on=on)

    # merge columns
    drop_cols = []
    for new_col in [col for col in df_merge.columns if col.endswith(suffix)]:
        col = new_col[:-4]
        df_merge[col] = df_merge[new_col].fillna(df_merge[col])
        drop_cols += [new_col]
    df_merge.drop(columns=drop_cols, inplace=True)
    return df_merge


def update_ctd_survey_station_lists(path='assets/ctd_survey_stations.parquet'):
    client = Client()
    response = client.get(
        f"{client.api_root}/ctd/views/file/cast?"
        f"fields=organization,work_area,cruise,station&limit=-1&distinct"
    )
    response.raise_for_status()
    df = pd.DataFrame(response.json())
    df.to_parquet(path)

def update_nutrients_survey_station_lists(path='assets/nutrients_survey_stations.parquet'):
    client = Client()
    response = client.get(
        f"{client.api_root}/eims/views/output/nutrients?"
        f"fields=organization,work_area,survey,site_id&limit=-1&distinct"
    )
    response.raise_for_status()
    df = pd.DataFrame(response.json())
    df.to_parquet(path)

def update_survey_stations_lists(path=None):
    update_ctd_survey_station_lists(path)
    update_nutrients_survey_station_lists(path)

if __name__ == "__main__":
    update_survey_stations_lists()