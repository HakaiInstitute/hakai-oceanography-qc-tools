import pandas as pd
from ioos_qc import qartod
from ioos_qc.config import Config
from ioos_qc.qartod import qartod_compare
from ioos_qc.stores import PandasStore
from ioos_qc.streams import PandasStream
from loguru import logger

default_axe_variables = dict(time="time", z="depth", lat="lat", lon="lon")


def qc_dataframe(df, configs, groupby=None, axes=None):
    """Run ioos_qc on subsets of a dataframe"""
    result_store = []
    if configs is not dict:
        config = {"": configs}
    if axes is None:
        axes = default_axe_variables
    else:
        default_axe_variables.update(axes)

    logger.debug("qc nutrient dataframe.index.name={}, df={}", df.index.name, df)
    original_columns = df.columns
    for query, config in configs.items():
        result_store = []
        df_subset = df.query(query)[original_columns]
        logger.info("run qc on query: {} = len(df)={}", query, len(df_subset))
        for group, timeserie in df_subset.groupby(groupby, as_index=False):
            # Make sure that the timeseries are sorted chronologically
            timeserie = timeserie.reset_index()
            # logger.debug("timeseries to be qc len(df)={}: {}", len(timeserie),timeserie)
            stream = PandasStream(timeserie, **axes)
            results = stream.run(Config(config))

            store = PandasStore(results, axes=axes)
            result_store += [
                timeserie.join(store.save(write_data=False, write_axes=False))
            ]

        df_qced = pd.concat(result_store, ignore_index=True)
        df = update_dataframe(df, df_qced, on="hakai_id")

    return df


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
