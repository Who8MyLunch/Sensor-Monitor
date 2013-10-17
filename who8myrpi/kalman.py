
from __future__ import division, print_function, unicode_literals

import matplotlib.pyplot as plt
import numpy as np
# import pandas as pd

import data_store
import arrow

import pykalman
import pykalman.sqrt


def index_to_seconds(index, t0=0):
    seconds = arrow.get(index).timestamp
    micro = arrow.get(index).datetime.microsecond

    seconds = float(seconds)
    micro = float(micro)

    seconds += micro * 1.e-6

    if t0:
        seconds -= t0

    return seconds


def dataframe_seconds(df, t0=0):
    """Convert Pandas TimeStampIndex to epoch seconds.
    """
    # seconds = [arrow.get(val).timestamp for val in df.index]
    # micro = [arrow.get(val).datetime.microsecond for val in df.index]

    seconds = [index_to_seconds(val, t0) for val in df.index]
    seconds = np.asarray(seconds, dtype=np.float)

    return seconds


def linear_model(x, y, num_resample=100):
    """
    Solve linear model, with bootstrapping to estimate parameter variances.
    Model: y = a0 + a1*x
    Return estimates for means and standard deviations of a0 and a1.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    num_samples = len(x)
    A = np.vstack([x, np.ones(num_samples)]).T

    a0_work = []
    a1_work = []
    for k in range(num_resample):
        ix = np.random.choice(num_samples, int(num_samples/2), replace=False)

        model = np.linalg.lstsq(A[ix], y[ix])
        a1, a0 = model[0]

        a0_work.append(a0)
        a1_work.append(a1)

    # Statistics from ensemble results.
    a0 = np.mean(a0_work)
    a0_std = np.std(a0_work)
    a1 = np.mean(a1_work)
    a1_std = np.std(a1_work)

    return a0, a1, a0_std, a1_std

#################################################

# Setup.

# data_store.update()
df = data_store.load()


# Work/test data
# pins = np.unique(df.Pin.values)
p = 25
mask_pins = df.Pin == p
df_all = df[mask_pins]['2013-10-11':'2013-10-12']


#################################################
# Initialize model using leading data.
t0 = index_to_seconds(df_all.index[0])

time_a, time_b = arrow.get(df_all.index[0]).span('hour')

fmt = 'YYYY-MM-DD HH:mm:ss'
df_init = df_all[time_a.format(fmt):time_b.format(fmt)]
df_work = df_all[time_b.format(fmt):]

seconds_all = dataframe_seconds(df_all, t0)
seconds_init = dataframe_seconds(df_init, t0)
seconds_work = dataframe_seconds(df_work, t0)

# Linear model fit.
H0, H1, H0_std, H1_std = linear_model(seconds_init, df_init.Humidity.values, 500)
T0, T1, T0_std, T1_std = linear_model(seconds_init, df_init.Temperature.values, 500)

# Configure the Kalman filter.
# state = [V, dV/dt]

# Time step.
dt = 10.  # sec.

# Dimensions.
d_state = 2
d_obs = 1

# Variances
var_trans = 0.01**2   # 1% of either signal, T or RH.
var_obs = H0_std**2

# Transition matrix and covariance.
A_trans = np.asarray([[1., dt],
                      [0., 1.]])

Q_trans_cov = np.eye(d_state) * var_trans

# Observation matrix and covariance.
C_obs = np.asarray([[1., 0.]])

R_obs_cov = np.eye(d_obs) * var_obs

# Initial state parameters.
state_init_avg = np.asarray([H0, H1])

state_init_cov = np.asarray([[H0_std, 0.],
                             [0., H1_std]])

kf = pykalman.KalmanFilter(transition_matrices=A_trans,
                           transition_covariance=Q_trans_cov,
                           observation_matrices=C_obs,
                           observation_covariance=R_obs_cov,
                           initial_state_mean=state_init_avg,
                           initial_state_covariance=state_init_cov)


# Display.
if True:
    fig = plt.figure(1)
    fig.clear()

    ax = fig.add_subplot(1, 1, 1)

    # Humidity.
    ax.plot(df_all.index, df_all.Humidity, label='H {:02d}'.format(p), color='blue')

    s = dataframe_seconds(df_init, t0)[[0, -1]]
    x = df_init.index[[0, -1]]
    y = H0 + H1*s
    ax.plot(x, y, label='H fit', color='orange')

    # Temperature.
    ax.plot(df_all.index, df_all.Temperature, label='T {:02d}'.format(p), color='red')

    y = T0 + T1*s
    ax.plot(x, y, label='T fit', color='green')

    ax.set_xlabel('Date / Time')
    ax.set_ylabel('Data')
    ax.legend(loc=2)

    plt.draw()

    plt.show()
