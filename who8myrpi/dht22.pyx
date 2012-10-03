
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

#######################################

cdef int count_ticks_low_high(int pin_data, int delta_time):
    """
    Number of ticks that signal stays down.
    """
    cdef int count_timeout = 1000000
    cdef int count_wait = 0
    cdef int count_high = 0
    cdef int count_low = 0
    cdef int value = 0
    
    # While not ready.
    while digitalRead(pin_data) == HIGH:
        delayMicroseconds(delta_time)
        count_wait += 1
        if count_wait >= count_timeout:
            return 0
            
    # While LOW, indicate new signal bit.
    while digitalRead(pin_data) == LOW:
        delayMicroseconds(delta_time)
        count_low += 1
        
    # While HIGH, duration of HIGH indicates bit value, 0 or 1.
    while digitalRead(pin_data) == HIGH:
        delayMicroseconds(delta_time)
        count_high += 1
    
        if count_high >= count_timeout:
            return 0
            
    # Determine signal value.
    value = count_high - count_low
    
    # Done.
    return value

    
        
        
def read(int pin_data, int delta_time):
    """
    Read data from DHT22 sensor.
    """

    val = wiringPiSetupGpio()
    if val < 0:
        raise Exception('Problem seting up WiringPI.')

    # Storage.
    cdef int num_data = 100
    data = np.zeros(num_data, dtype=np.int)
    cdef int [:] data_view = data

    cdef int count = 0
    cdef int value = 0
    
    #
    # Send start signal to sensor.
    #

    # Set pin to output mode.
    pinMode(pin_data, OUTPUT)

    # Set pin low.
    digitalWrite(pin_data, LOW)

    # Wait 10 milliseconds, long enough for sensor to see start signal.
    delayMicroseconds(10)

    # Set pin high, indicate ready to receive data from sensor.
    digitalWrite(pin_data, HIGH)
    
    #
    # Read responses from sensor.
    #
    pinMode(pin_data, INPUT)

    # Main loop reading from sensor.
    while count < num_data:
        value = count_ticks_low_high(pin_data, delta_time)
        if value == 0:
            break
            
        data_view[count] = value
        count += 1


    # Done.
    return data



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
    cdef int time_elapsed
    cdef int num_cycles
    cdef int time_now

    time_run *= 1000 # Convert to milliseconds.
    time_start = millis()
    time_elapsed = 0
    num_cycles = 0

    while time_elapsed < time_run:
        time_now = millis()
        time_elapsed = time_now - time_start
        num_cycles += 1

        # Read from switch.
        val = digitalRead(pin_switch)
        val = digitalRead(pin_switch)
        val = digitalRead(pin_switch)

        # data_view[0] = val
        data[0] = val

        delayMicroseconds(delay)

    dt = float(time_run) / float(num_cycles) *1.e3
    print(dt)

    # Done
    return num_cycles



