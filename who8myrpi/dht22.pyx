
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


 
def read(int pin_data):
    """
    Read data from DHT22 sensor.
    """

    # Storage.
    num_data = 10000
    data = np.zeros(num_data, dtype=np.int)
    cdef int [:] data_view = data

    #
    # Send start signal to sensor.
    #
    
    # Set pin to output mode.
    pinMode(pin_data, OUTPUT)
    
    # Set pin low.
    digitalWrite(pin_data, LOW)
    
    # Wait 20 milliseconds.
    delayMicroseconds(20)
    
    # Set pin high.
    digitalWrite(pin_data, HIGH)
    
    #
    # Read response from sensor.
    #
    pinMode(pin_data, INPUT)

    # Main loop reading from sensor.
    ok = True
    cdef int val
    cdef int k = 0
    while ok:
        val = digitalRead(pin_data)
        data_view[k] = val

        
        # End of loop.
        if k >= num_data-10:
            break
            
        k += 1
        
        
        
        
    # Done.
    return data
    
    
        
##########################################

def timing_example(int time_run, unsigned int delay):
    """
    time_run in seconds.
    
    cython arraview: http://docs.cython.org/src/userguide/memoryviews.html
    
    """

    val = wiringPiSetupGpio()
    
    data = np.zeros(100, dtype=np.int)
    cdef int [:] data_view = data
    
    
    if val < 0:
        raise Exception('Problem seting up WiringPI.')

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
        
        data_view[0] = val
        
        delayMicroseconds(delay)
        
    dt = float(time_run) / float(num_cycles) *1.e3
    print(dt)
    
    # Done
    return num_cycles
    
    
    
   