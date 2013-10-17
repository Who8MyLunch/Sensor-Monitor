
from __future__ import division, print_function, unicode_literals

import matplotlib.pyplot as plt
import numpy as np
# import pandas as pd

import data_store
import arrow
import pykalman


def dataframe_seconds(df, t0=0.):
    """Convert Pandas TimeStampIndex to epoch seconds.
    """
    seconds = [arrow.get(val).timestamp for val in df.index]
    micro = [arrow.get(val).datetime.microsecond for val in df.index]

    seconds = np.asarray(seconds, dtype=np.float)
    micro = np.asarray(micro, dtype=np.float)

    seconds += micro * 1.e-6

    if t0:
        seconds -= t0

    return seconds


#################################################
# Setup.

# data_store.update()
df = data_store.load()


# Work/test data
# pins = np.unique(df.Pin.values)
p = 25
mask_pins = df.Pin == p
df_work = df[mask_pins]['2013-10-11':'2013-10-12']

# Initialize state using leading data.
time_a, time_b = arrow.get(df_work.index[0]).span('hour')

fmt = 'YYYY-MM-DD HH:mm:ss'
df_init = df_work[time_a.format(fmt):time_b.format(fmt)]

seconds = dataframe_seconds(df_init)
t0 = seconds.min()
seconds -= t0

T = df_init.Temperature
H = df_init.Humidity

num_samples = len(H)
A = np.vstack([seconds, np.ones(num_samples)]).T

rates = []
values = []
for k in range(500):
    ix = np.random.choice(num_samples, int(num_samples/2), replace=False)

    model = np.linalg.lstsq(A[ix], H.values[ix])
    rate, value = model[0]

    rates.append(rate)
    values.append(value)

rate_avg = np.mean(rates)
rate_std = np.std(rates)
value_avg = np.mean(values)
value_std = np.std(values)

state_avg = np.asarray([rate_avg, value_avg])
state_cov = np.asarray([[rate_std, 0.0],
                        [0.0, value_std]])






state_pdf = pybayes.GaussPdf(state_avg, state_cov)

dt = 1.5  # seconds
model_process = np.asarray([[1., dt],
                            [0., 1.]])
covar_process = state_cov.copy()

model_observation = np.asarray([[0., 1.]])
covar_observation = rate_std.reshape(1, 1)

kf = pybayes.KalmanFilter(A=model_process,
                          C=model_observation,
                          Q=covar_process,
                          R=covar_observation,
                          state_pdf=state_pdf)
obs = np.asarray([52.])
kf.bayes(obs)

# Display.
if True:
    fig = plt.figure(1)
    fig.clear()

    ax = fig.add_subplot(1, 1, 1)
    # ax.plot(df_init.index, df_init.Humidity, label='H {:02d}'.format(p))
    ax.plot(seconds, df_init.Humidity, label='H {:02d}'.format(p))
    ax.plot(seconds, value + rate*seconds, label='fit')

    ax.set_xlabel('Date / Time')
    ax.set_ylabel('Data')
    ax.legend(loc=2)

    plt.draw()

    plt.show()
