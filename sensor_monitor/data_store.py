
from __future__ import division, print_function, unicode_literals

"""
Manage data between Google Fusion Table and local HDF files.

The ideal situation would be a transparant data fetch operation.
Suppose I want data from a certain range of days.

This module would support the following basic functions:
  - Check to see if data is available locally
  - Fetch data from Fusion Table
  - Store data locally
  - Fetch data locally
  - Update local data with changes and/or new samples

Utility functions:
  - Summary of data in local storage (e.g. days)
"""

import os
import datetime
import glob

import numpy as np
import pandas as pd
import arrow

import download
import master_table
import utility


def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p


_folder_store = 'data_storage'


def dates_in_storage():
    """Return list of dates found in storage.
    """
    pattern = os.path.join(path_to_module(), _folder_store, 'data_????-??-??.h5')
    files = glob.glob(pattern)

    dates = []
    for f in files:
        b, e = os.path.splitext(os.path.basename(f))
        c = b.split('data_')[1]

        year, month, day = c.split('-')
        date = arrow.Arrow(int(year), int(month), int(day))
        dates.append(date)

    return sorted(dates)


def daterange(start_date, end_date):
    """Date range generator.
    """
    num_days = int((end_date - start_date).days)
    for n in range(num_days):
        yield start_date + datetime.timedelta(n)


def update(year_start=None, month_start=None, day_start=None):
    """
    Update local data store from Google Fusion Table.

    Default start date equal to day of most recent data in storage.
    """

    dates = dates_in_storage()
    if dates:
        date_latest = max(dates)
    else:
        year_start = 2013
        month_start = 8
        day_start = 1

    # Start time, US/Pacific time.
    if not year_start:
        year_start = date_latest.year

    if not month_start:
        month_start = date_latest.month

    if not day_start:
        day_start = date_latest.day

    # End time, US/Pacific time.
    date_tomorrow = arrow.now().replace(days=1)
    year_end = date_tomorrow.year
    month_end = date_tomorrow.month
    day_end = date_tomorrow.day

    #
    # Download data from Google in one big chunk.
    #
    seconds_start = utility.timestamp_seconds(year_start, month_start, day_start)
    seconds_end = utility.timestamp_seconds(year_end, month_end, day_end)

    pretty_start = utility.pretty_timestamp(seconds_start)
    pretty_end = utility.pretty_timestamp(seconds_end)

    print('Start: {:s}'.format(pretty_start))
    print('End:   {:s}'.format(pretty_end))

    table_id = master_table.get_current_table_id()
    print('Fetch data from Fusion Table: {:s}'.format(table_id))

    data_table = download.data_between(table_id, seconds_start, seconds_end)

    #
    # Extract data, store in Pandas DataFrame.
    #
    print('Process data...')
    ix_seconds = 1
    ix_pin = 3
    ix_T = 4
    ix_RH = 5

    # Convert data seconds to a handy timestamp (US/Pacific) index.
    seconds = [row[ix_seconds] for row in data_table]
    timestamps = [utility.datetime_seconds(s) for s in seconds]
    timestamps_index = pd.DatetimeIndex(timestamps)

    # Extract data columns.
    col_pin = np.asarray([row[ix_pin] for row in data_table], dtype=np.uint8)
    col_T = np.asarray([row[ix_T] for row in data_table], dtype=np.float32)
    col_RH = np.asarray([row[ix_RH] for row in data_table], dtype=np.float32)

    data_dict = {'Pin': col_pin, 'Temperature': col_T, 'Humidity': col_RH}

    data_frame = pd.DataFrame(data_dict, index=timestamps_index)

    pins = np.unique(data_frame.Pin).values
    print('GPIO pins: {:s}'.format(str(pins)))

    #
    # Main loop over days of data.
    #
    dt_start = utility.datetime_seconds(seconds_start)
    dt_end = utility.datetime_seconds(seconds_end)

    path_store = os.path.join(path_to_module(), _folder_store)
    if not os.path.isdir(path_store):
        os.makedirs(path_store)

    for date_k in daterange(dt_start, dt_end):
        date_filter = date_k.strftime("%Y-%m-%d")

        try:
            # One day of data.
            df_k = data_frame[date_filter]

            # Save to file.
            fname = 'data_{:s}.h5'.format(date_filter)
            f = os.path.join(path_store, fname)

            if df_k.shape[0]:
                print(date_filter, df_k.shape)
                df_k.to_hdf(f, 'df', table=True)

        except KeyError:
            pass


def load():
    """Load all data from storage.
    """
    pattern = os.path.join(path_to_module(), _folder_store, 'data_????-??-??.h5')
    files = glob.glob(pattern)

    if not files:
        raise ValueError('No data found in storage.')

    data = []
    for f in files:
        df_k = pd.read_hdf(f, 'df')
        data.append(df_k)

    data_frame = pd.concat(data).sort()
    # pins = np.unique(data_frame.Pin).values

    return data_frame

#################################################


if __name__ == '__main__':
    """
    Examples.
    """

    print('Update data storage.')
    update()
