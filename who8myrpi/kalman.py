
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


def linear_model(x, y, num_resample=500):
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

# Linear model fit for initial state.
# H0, H1, H0_std, H1_std = linear_model(seconds_init, df_init.Humidity.values)
# T0, T1, T0_std, T1_std = linear_model(seconds_init, df_init.Temperature.values)

H0 = df_init.Humidity.values.mean()
H1 = 0.0
H0_std = 0.02
H1_std = 1.e-5

T0 = df_init.Temperature.values.mean()
T1 = 0.0
T0_std = 0.02
T1_std = 1.e-6

# Statistics for observation variances.
H0_obs_std = 1.0  # np.std(df_init.Humidity.values)
T0_obs_std = 0.5  # np.std(df_init.Temperature.values) * 10

# Initial data, assuming regular sampling.
dt = (seconds_init.max() - seconds_init.min()) / (len(seconds_init) - 1.)

# State vector.
# state = [H, dH/dt, T, dT/dt]

# Transition matrix and covariance.
g = lambda x: x**2

A_trans_func = lambda dt: np.asarray([[1., dt, 0., 0.],
                                      [0., 1., 0., 0.],
                                      [0., 0., 1., dt],
                                      [0., 0., 0., 1.]])
A_trans = A_trans_func(dt)
# A_trans = np.asarray([[1., dt, 0., 0.],
#                       [0., 1., 0., 0.],
#                       [0., 0., 1., dt],
#                       [0., 0., 0., 1.]])

Q_trans_cov = np.asarray([[H0_std**2, 0., 0., 0.],
                          [0., H1_std**2, 0., 0.],
                          [0., 0., T0_std**2, 0.],
                          [0., 0., 0., T1_std**2]])

# Observation matrix and covariance.
C_obs = np.asarray([[1., 0., 0., 0.],
                    [0., 0., 1., 0.]])

R_obs_cov = np.asarray([[H0_obs_std**2, 0.],
                        [0., T0_obs_std**2]])

# Initial state parameters.
state_init_avg = np.asarray([H0, 0., T0, 0.])

# state_init_cov = np.asarray([[H0_std**2, 0.],
#                              [0., H1_std**2],
#                              [T0_std**2, 0.],
#                              [0., T1_std**2]])
state_init_cov = np.eye(4)

kf = pykalman.sqrt.BiermanKalmanFilter(transition_matrices=A_trans,
                                       observation_matrices=C_obs,
                                       transition_covariance=Q_trans_cov,
                                       observation_covariance=R_obs_cov,
                                       initial_state_mean=state_init_avg,
                                       initial_state_covariance=state_init_cov)

X_init = np.vstack((df_init.Humidity.values, df_init.Temperature.values)).T
X_all = np.vstack((df_all.Humidity.values, df_all.Temperature.values)).T


print(kf.observation_covariance)
print(kf.transition_covariance)

em_vars = ['initial_state_covariance', 'initial_state_mean',
           'transition_covariance', 'observation_covariance']

kf = kf.em(X_init, em_vars=em_vars)
kf.observation_covariance[0, 0] = R_obs_cov[0, 0]
kf.observation_covariance[1, 1] = R_obs_cov[1, 1]

print()
print(kf.observation_covariance)
print(kf.transition_covariance)

states_avg, states_cov = kf.filter(X_init)
t_km1 = seconds_init.max()

state_avg_km1 = states_avg[-1]
state_cov_km1 = states_cov[-1]

# Loop over data observations.
H_filtered = []
for k in range(df_all.shape[0]):

    ix_k = df_all.index[k]
    t_k = index_to_seconds(ix_k, t0)
    dt = t_k - t_km1
    A_trans = A_trans_func(dt)

    T_k = df_all.Temperature[k]
    H_k = df_all.Humidity[k]

    X_k = np.asarray([H_k, T_k])

    state_avg_k, state_cov_k = kf.filter_update(state_avg_km1, state_cov_km1,
                                                observation=X_k,
                                                transition_matrix=A_trans)

    # print(k, dt, state_avg_k[0], state_avg_k[2])

    t_km1 = t_k
    state_avg_km1 = state_avg_k
    state_cov_km1 = state_cov_k[0]

    H_filtered.append(state_avg_k[0])

# Display.
if True:
    fig = plt.figure(1)
    fig.clear()

    ax = fig.add_subplot(1, 1, 1)

    # Humidity.
    ax.plot(df_all.index, df_all.Humidity, label='H {:02d}'.format(p), color='blue')

    ax.plot(df_all.index, H_filtered, label='H', color='purple')
    # ax.plot(df_all.index, states_mean2[:, 0], label='H 2', color='green', linewidth=2)

    # Temperature.
    ax.plot(df_all.index, df_all.Temperature, label='T {:02d}'.format(p), color='red')

    # y = T0 + T1*s
    # ax.plot(x, y, label='T fit', color='green')

    # ax.plot(df_init.index, states_mean[:, 2], label='T 1', color='purple')
    # ax.plot(df_all.index, states_mean2[:, 2], label='T 2', color='green', linewidth=2)
    ax.set_xlabel('Date / Time')
    ax.set_ylabel('Data')

    ax.legend(loc=3)

    plt.draw()

    plt.show()
