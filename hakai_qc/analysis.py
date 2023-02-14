import pandas as pd

def get_interannual_variability(data,groupby,time_grid='14D'):
    # Reseample data to a standard grid for each year starting on Jan 1st. Average values within the same grid
    grid_window = '14D'
    df_resampled = pd.DataFrame()
    resampled = []
    for index,df_group in data.groupby(groupby):
        df_temp = df_group.resample(grid_window,on='time',origin=pd.to_datetime(f"{index[1]}-01-01 00:00:00")).mean(numeric_only=True)
        df_temp[groupby] = index
        resampled += [df_temp]

    df_resampled = pd.concat(resampled).reset_index()
    df_resampled['dayoftheyear'] = df_resampled['time'].dt.dayofyear

    # For each similar day of the year compute the interannual variability
    df_interannual = df_resampled.drop(columns=['time']).groupby(['site_id','reference_depth','dayoftheyear']).agg(['mean','std']).reset_index()

    # Center each window pandas resample give start of the window
    df_interannual['dayoftheyear'] = df_interannual['dayoftheyear'] + pd.to_timedelta(grid_window).days/2 

    return df_interannual
