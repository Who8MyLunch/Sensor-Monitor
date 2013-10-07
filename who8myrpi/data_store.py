
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

Metadata:
  - Parameters from last Fusion Table fetch (e.g. date range of returned data)

"""
import os
import datetime
import numpy as np
import pandas as pd

import download
import master_table
import utility

PATH_STORE = os.path.join(os.path.dirname(__file__), 'data_store')


# Date range generator.
def daterange(start_date, end_date):
    num_days = int((end_date - start_date).days)
    for n in range(num_days):
        yield start_date + datetime.timedelta(n)

#################################################

# Start and end time, US/Pacific time.
year_start = 2013
month_start = 8
day_start = 1

year_end = 2013
month_end = 10
day_end = 5

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
print('Make DataFrame...')
ix_seconds = 1
ix_pin = 3
ix_T = 4
ix_RH = 5

# Convert data seconds to a timestamp (US/Pacific) index.
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

# Loop over days of data.
dt_start = utility.datetime_seconds(seconds_start)
dt_end = utility.datetime_seconds(seconds_end)

if not os.path.isdir(PATH_STORE):
    os.makedirs(PATH_STORE)

for date_k in daterange(dt_start, dt_end):
    date_filter = date_k.strftime("%Y-%m-%d")

    try:
        # One day of data.
        df_k = data_frame[date_filter]

        # Save to file.
        fname = 'data_{:s}.h5'.format(date_filter)
        f = os.path.join(PATH_STORE, fname)

        if df_k.shape[0]:
            print(date_filter, df_k.shape)
            df_k.to_hdf(f, 'df_k', table=True)

    except KeyError:
        pass
