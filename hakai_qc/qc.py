import logging

import pandas as pd
from ioos_qc import qartod
from ioos_qc.config import Config
from ioos_qc.stores import PandasStore
from ioos_qc.streams import PandasStream
from ioos_qc.qartod import qartod_compare

logger = logging.getLogger(__name__)
default_axe_variables = dict(time="time", z="depth", lat="lat", lon="lon")


def qc_dataframe(df, configs, groupby=None, axes=None):
    result_store = []
    if configs is not dict:
        config = {"": configs}
    if axes is None:
        axes = default_axe_variables
    else:
        default_axe_variables.update(axes)

    logger.debug("Use axes: %s", axes)
    logger.debug("dataframe dtypes: %s", df.dtypes)
    logger.debug("qc len(df)=%s", len(df))
    for query, config in configs.items():
        df_subset = df.query(query)
        logger.info("run qc on query: %s = len(df)=%s", query, len(df_subset))
        for group, timeserie in df_subset.groupby(groupby, as_index=False):
            # Make sure that the timeseries are sorted chronologically

            logger.debug("timeseries to qc len(df)=%s", len(timeserie))
            stream = PandasStream(timeserie.reset_index(), **axes)
            results = stream.run(Config(config))

            store = PandasStore(results, axes=axes)
            result_store += [
                timeserie.join(store.save(write_data=False, write_axes=False))
            ]
            logger.debug("result_stored %s: %s", group, len(result_store[-1]))

    return pd.concat(result_store, ignore_index=True)
