import pandas as pd


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
