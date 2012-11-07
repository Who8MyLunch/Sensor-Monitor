
from __future__ import division, print_function, unicode_literals

import matplotlib.pyplot as plt
import numpy as np
import data_io as io

############
# Setup.

fname_data = 'sensor_data.npz'
data, meta = io.read(fname_data)

dt = 1.5
t_end = dt*len(data)
x = np.arange(0, t_end, dt, dtype=np.float)

#
# Display.
#
fig = plt.figure(1)
fig.clear()

ax = fig.add_subplot(1, 1, 1)
ax.plot(x, data)

ax.set_ylim(0, 1.2)
ax.set_xlim(0, 4500)

ax.set_xlabel('Samples')
ax.set_ylabel('Signal Level')

plt.tight_layout()
plt.draw()

plt.show()

# Done.
