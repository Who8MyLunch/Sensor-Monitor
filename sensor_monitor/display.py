
from __future__ import division, print_function, unicode_literals

import matplotlib.pyplot as plt
import numpy as np
# import pandas as pd

import data_store

#################################################
# Setup.

# data_store.update()
df = data_store.load()

pins = np.unique(df.Pin.values)


fig = plt.figure(1)
fig.clear()

ax = fig.add_subplot(1, 1, 1)

for p in pins:
    mask = df.Pin == p
    ax.plot(df[mask].index, df[mask].Humidity, label='H {:02d}'.format(p))
    ax.plot(df[mask].index, df[mask].Temperature, label='T {:02d}'.format(p))

ax.set_xlabel('Date / Time')
ax.set_ylabel('Data')
ax.legend(loc=2)

plt.draw()

plt.show()
