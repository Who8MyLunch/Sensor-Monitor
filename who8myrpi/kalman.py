
from __future__ import division, print_function, unicode_literals

import matplotlib.pyplot as plt
import numpy as np
# import pandas as pd

import data_store
import arrow
import pybayes


def index_to_seconds(index):
    seconds = arrow.get(index).timestamp
    micro = arrow.get(index).datetime.microsecond

    seconds = float(seconds)
    micro = float(micro)

    seconds += micro * 1.e-6

    return seconds


def dataframe_seconds(df, t0=0.):
    """Convert Pandas TimeStampIndex to epoch seconds.
    """
    # seconds = [arrow.get(val).timestamp for val in df.index]
    # micro = [arrow.get(val).datetime.microsecond for val in df.index]

    seconds = [index_to_seconds(val) for val in df.index]
    seconds = np.asarray(seconds, dtype=np.float)

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
df_all = df[mask_pins]['2013-10-11':'2013-10-12']

# Initialize model using leading data.
fmt = 'YYYY-MM-DD HH:mm:ss'
time_a, time_b = arrow.get(df_all.index[0]).span('hour')

df_init = df_all[time_a.format(fmt):time_b.format(fmt)]
df_work = df_all[time_b.format(fmt):]

seconds_all = dataframe_seconds(df_all)
seconds_init = dataframe_seconds(df_init)

t0 = seconds_all.min()
seconds_all -= t0
seconds_init -= t0

T = df_init.Temperature
H = df_init.Humidity

num_samples = len(H)
A = np.vstack([seconds_init, np.ones(num_samples)]).T

rates = []
values = []
for k in range(500):
    ix = np.random.choice(num_samples, int(num_samples/2), replace=False)

    model = np.linalg.lstsq(A[ix], H.values[ix])
    rate, value = model[0]

    rates.append(rate)
    values.append(value)

# Statistics from initial data.
rate_avg = np.mean(rates)
rate_std = np.std(rates)
value_avg = np.mean(values)
value_std = np.std(values)

# Statistics about hidden state.
state_avg = np.asarray([value_avg, rate_avg])

signal_std = 0.1
signal_rate_std = 0.05  # ???
state_cov = np.asarray([[signal_std, 0.0],
                        [0.0, signal_rate_std]])


#
time_a = index_to_seconds(df_init.index[-1]) - t0
time_b = index_to_seconds(df_work.index[0]) - t0

value_init = np.asarray([value_avg + rate_avg*time_a, rate_avg])
state_pdf = pybayes.GaussPdf(value_init, state_cov)


dt = time_b - time_a
A_transition = np.asarray([[1., dt],
                           [0., 1.]])
Q_covar_trans = state_cov  # I don't know why this should be different from state_cov

C_data = np.asarray([[1., 0.]])
R_covar_data = value_std.reshape(1, 1)

kf = pybayes.KalmanFilter(A=A_transition,
                          C=C_data,
                          Q=Q_covar_trans,
                          R=R_covar_data,
                          state_pdf=state_pdf)
obs = np.asarray(df_work.Humidity[0]).reshape(1).astype(np.float)

kf.bayes(obs)

value_pred = kf.posterior().mean()[0]

# Display.
if True:
    fig = plt.figure(1)
    fig.clear()

    ax = fig.add_subplot(1, 1, 1)
    # ax.plot(df_init.index, df_init.Humidity, label='H {:02d}'.format(p))
    ax.plot(seconds_all, df_all.Humidity, label='H {:02d}'.format(p))
    ax.plot(seconds_init, value_avg + rate_avg*seconds_init, label='fit')

    ax.set_xlabel('Date / Time')
    ax.set_ylabel('Data')
    ax.legend(loc=2)

    plt.draw()

    plt.show()
