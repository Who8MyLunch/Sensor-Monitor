
from __future__ import division, print_function, unicode_literals

import matplotlib.pyplot as plt
import numpy as np
# import pandas as pd

import data_store
import arrow
import pybayes


def dataframe_seconds(df, t0=0.):
    """Convert Pandas TimeStampIndex to epoch seconds.
    """
    seconds = [arrow.get(val).timestamp for val in df.index]
    micro = [arrow.get(val).datetime.microsecond for val in df.index]

    seconds = np.asarray(seconds, dtype=np.float32)
    micro = np.asarray(micro, dtype=np.float32)

    seconds += micro * 1.e-6

    if t0:
        seconds -= t0

    return seconds


#################################################
# Setup.

# data_store.update()
df = data_store.load()

# pins = np.unique(df.Pin.values)

# Work/test data
p = 25
mask_pins = df.Pin == p

df_work = df[mask_pins]['2013-10-11':'2013-10-12']

# Times from index.
# datetime = df[mask].index
# seconds = [arrow.get(val).timestamp + arrow.get(val).datetime.microsecond/1.e6 for val in datetime]
# seconds = np.asarray(seconds)
# t_0 = seconds.min()
# seconds -= t_0


# Initialize model using leading data.
fmt = 'YYYY-MM-DD HH:mm:ss'
time_a, time_b = arrow.get(df_work.index[0]).span('hour')

df_init = df_work[time_a.format(fmt):time_b.format(fmt)]

seconds = dataframe_seconds(df_init)
t0 = seconds.min()
seconds -= t0

T = df_init.Temperature
H = df_init.Humidity

num_samples = len(H)
A = np.vstack([seconds, np.ones(num_samples)]).T

model = np.linalg.lstsq(A, H.values)

# Display.
if False:
    fig = plt.figure(1)
    fig.clear()

    ax = fig.add_subplot(1, 1, 1)
    ax.plot(datetime, H, label='H {:02d}'.format(p))

    ax.set_xlabel('Date / Time')
    ax.set_ylabel('Data')
    ax.legend(loc=2)

    plt.draw()

    plt.show()
