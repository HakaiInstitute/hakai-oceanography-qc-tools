import logging
import os

import pandas as pd
import yaml
from dotenv import dotenv_values

logger = logging.getLogger(__name__)


def load_config():
    # Load configuration
    with open("default-config.yaml", encoding="UTF-8") as config_handle:
        config = yaml.load(config_handle, Loader=yaml.SafeLoader)
    config.update(
        {
            **dotenv_values(".env"),  # load shared development variables
            **os.environ,  # override loaded values with environment variables
        }
    )
    return config


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
