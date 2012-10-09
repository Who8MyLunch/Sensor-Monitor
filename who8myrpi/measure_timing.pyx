
from __future__ import division, print_function, unicode_literals

cimport cython

import numpy as np
cimport numpy as np

np.import_array()

import time

############################

cdef extern from 'wiringPi/wiringPi.h':
    cdef int wiringPiSetup()
    cdef int wiringPiSetupSys()
    cdef int wiringPiSetupGpio()
    cdef int wiringPiSetupPiFace()

    cdef void pinMode(int pin, int mode)
    cdef int  digitalRead(int pin)
    cdef void digitalWrite(int pin, int value)
    cdef void pullUpDnControl(int pin, int pud)
    cdef void setPadDrive(int group, int value)

    cdef void pwmSetMode(int mode)
    cdef void pwmWrite(int pin, int value)
    cdef void pwmSetRange(unsigned int range)

    cdef void delayMicroseconds(unsigned int howLong)
    cdef unsigned int millis()


# Constants.
cdef int LOW = 0
cdef int HIGH = 1

cdef int MODE_PINS  = 0
cdef int MODE_GPIO = 1
cdef int MODE_SYS = 2
cdef int MODE_PIFACE = 3

cdef int INPUT = 0
cdef int OUTPUT = 1
cdef int PWM_OUTPUT = 2

cdef int PUD_OFF = 0
cdef int PUD_DOWN = 1
cdef int PUD_UP = 2

cdef int PWM_MODE_MS = 0
cdef int PWM_MODE_BAL = 1

##########################################

def timing_example(int time_run, unsigned int delay):
    """
    time_run in seconds.

    cython arraview: http://docs.cython.org/src/userguide/memoryviews.html

    """
    val = wiringPiSetupGpio()
    if val < 0:
        raise Exception('Problem seting up WiringPI.')

    data = np.zeros(100, dtype=np.int)
    cdef int [:] data_view = data

    cdef int pin_switch = 21

    pinMode(pin_switch, INPUT)

    pullUpDnControl(pin_switch, PUD_DOWN)

    cdef int time_start
    cdef float time_start_py

    cdef int time_elapsed
    cdef float time_elapsed_py

    cdef int num_cycles

    cdef int time_now
    cdef float time_now_py
    cdef int value

    time_run *= 1000 # Convert to milliseconds.
    time_start = millis()
    time_start_py = time.clock()

    time_elapsed = 0
    num_cycles = 0

    while time_elapsed < time_run:
        time_now = millis()
        time_now_py = time.clock()

        time_elapsed = time_now - time_start
        time_elapsed_py = time_now_py - time_start_py

        num_cycles += 1

        # Read from switch.
        value = digitalRead(pin_switch)
        # value = digitalRead(pin_switch)
        # value = digitalRead(pin_switch)

        data_view[0] = value

        # Delay.
        # delayMicroseconds(delay)
        

    dt = float(time_elapsed) / float(num_cycles) *1.e3
    dt_py = time_elapsed_py / float(num_cycles) * 1.e6

    print('sample time:      %f microseconds' % dt)
    print('sample time (py): %f microseconds' % dt_py)

    # Done
    return num_cycles



