
from __future__ import division, print_function, unicode_literals

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import download
import master_table
import utility

#################################################
# Setup.
flag_display = True

# Start and end time.
year = 2013
month = 9
day = 18
hour = 19
minute = 0
time_start = utility.timestamp_seconds(year, month, day, hour, minute)

# hour = 20
# minute = 30
# time_end = utility.timestamp_seconds(year, month, day, hour, minute)

#################################################
# Fetch data.
table_id = master_table.get_current_table_id()

print('Download data from table: {:s}'.format(table_id))

data_orig = download.data_between(table_id, time_start)


ix_seconds = 1
ix_id = 3
ix_T = 4
ix_RH = 5

names = ['id', 'temperature', 'humidity']

datetimes = [utility.datetime_seconds(row[ix_seconds]) for row in data_orig]
timestamps = pd.DatetimeIndex(datetimes)

data_id = [int(row[ix_id]) for row in data_orig]
data_T = [float(row[ix_T]) for row in data_orig]
data_RH = [float(row[ix_RH]) for row in data_orig]

data_dict = {'ID': data_id, 'Temperature': data_T, 'Humidity': data_RH}

data_frame = pd.DataFrame(data_dict, index=timestamps)

pins = np.unique(data_frame.ID).values

data_work = data_frame['2013-09-21 00:00':'2013-09-28 00:00']

#################################################
# Display.
if flag_display:
    fig = plt.figure(1)
    fig.clear()

    ax = fig.add_subplot(1, 1, 1)

    for ID in pins:
        mask = data_work.ID == ID
        ax.plot(data_work[mask].index, data_work[mask].Humidity)
        ax.plot(data_work[mask].index, data_work[mask].Temperature)

    ax.set_xlabel('Date / Time')
    ax.set_ylabel('T / RH')

    plt.draw()

    plt.show()
