
from __future__ import division, print_function, unicode_literals

cimport cython

import numpy as np
cimport numpy as np

np.import_array()

import time

############################

cdef extern from 'wiringPi/wiringPi.h':
    cdef int wiringPiSetup() nogil
    cdef int wiringPiSetupSys() nogil
    cdef int wiringPiSetupGpio() nogil
    cdef int wiringPiSetupPiFace() nogil

    cdef void pinMode(int pin, int mode) nogil
    cdef int  digitalRead(int pin) nogil
    cdef void digitalWrite(int pin, int value) nogil
    cdef void pullUpDnControl(int pin, int pud) nogil
    cdef void setPadDrive(int group, int value) nogil

    cdef void pwmSetMode(int mode) nogil
    cdef void pwmWrite(int pin, int value) nogil
    cdef void pwmSetRange(unsigned int range) nogil

    cdef void delay(unsigned int howLong) nogil
    cdef void delayMicroseconds(unsigned int howLong) nogil
    cdef unsigned int millis() nogil


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

@cython.boundscheck(False)
@cython.wraparound(False)
def timing(int pin=21, int time_poll=10):
    """
    Measure sample timing while reading values from specified pin.
    time_poll = number of milliseconds to record data.
    """
    val = wiringPiSetupGpio()
    if val < 0:
        raise Exception('Problem seting up WiringPI.')

    data = np.zeros(5, dtype=np.int)
    cdef int [:] data_view = data

    # Set pin modes.
    pinMode(pin, INPUT)
    pullUpDnControl(pin, PUD_DOWN)

    # Initialize times and counters.
    cdef int time_start = 0
    cdef int time_now = 0
    cdef int time_elapsed = 0
    cdef int counter = 0
    cdef int value = 0
    
    # Main loop.
    counter = 0
    time_start = millis()
    time_elapsed = 0
    with nogil:
        while time_elapsed <= time_poll:
            counter += 1
            time_now = millis()
            time_elapsed = time_now - time_start

            # Read from pin, store value in Numpy array.
            value = digitalRead(pin)
            data_view[0] = value


    # Compute timing.
    cdef float time_sample = 0
    time_sample = float(time_elapsed) / float(counter)

    # Done.
    return time_sample



def timing_example(int time_run, unsigned int delay):
    """
    time_run in seconds.

    cython array view: http://docs.cython.org/src/userguide/memoryviews.html
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
        # time_now_py = time.clock()

        time_elapsed = time_now - time_start
        # time_elapsed_py = time_now_py - time_start_py

        num_cycles += 1

        # Read from switch.
        value = digitalRead(pin_switch)
        # value = digitalRead(pin_switch)
        # value = digitalRead(pin_switch)

        data_view[0] = value

        # Delay.
        # delayMicroseconds(delay)


    dt = float(time_elapsed) / float(num_cycles) *1.e3
    # dt_py = time_elapsed_py / float(num_cycles) * 1.e6

    print('sample time:      %f microseconds' % dt)
    # print('sample time (py): %f microseconds' % dt_py)

    # Done
    return num_cycles



