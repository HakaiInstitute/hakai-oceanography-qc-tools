import pandas as pd
from ioos_qc import qartod
from ioos_qc.config import Config
from ioos_qc.stores import PandasStore
from ioos_qc.streams import PandasStream

default_axe_variables = dict(time="time", z="depth", lat="lat", lon="lon")


def qc_dataframe(df, configs, groupby=None, axes=None):
    result_store = []
    if configs is not dict:
        config = {"": configs}
    if axes is None:
        axes = default_axe_variables
    else:
        axes = default_axe_variables.update(axes)

    for query, config in configs.items():
        df_depth_range = df.query(query)
        for group, timeserie in df_depth_range.groupby(groupby, as_index=False):
            # Make sure that the timeseries are sorted chronologically
            if "time" in axes:
                timeserie = timeserie.sort_values(axes["time"]).reset_index()

            stream = PandasStream(timeserie, **axes)
            results = stream.run(Config(config))

            store = PandasStore(results, axes=axes)
            result_store += [
                timeserie.join(store.save(write_data=False, write_axes=False))
            ]

    return pd.concat(result_store, ignore_index=True)
