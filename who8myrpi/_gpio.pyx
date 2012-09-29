
from __future__ import division, print_function, unicode_literals

cimport cython

import numpy as np
cimport numpy as np

np.import_array()

############################

cdef extern from 'wiringPi/wiringPi.h':
    cdef int wiringPiSetup()
    cdef int wiringPiSetupSys()
    cdef int wiringPiSetupGpio()
    cdef int wiringPiSetupPiFace()

    cdef void pinMode(int pin, int mode)
    cdef void pullUpDnControl(int pin, int pud)
    cdef void digitalWrite(int pin, int value)
    cdef void setPadDrive(int group, int value)
    cdef int  digitalRead(int pin)

    cdef void delayMicroseconds(unsigned int howLong)
    cdef unsigned int millis()

    cdef void pwmSetMode(int mode)
    cdef void pwmWrite(int pin, int value)
    cdef void pwmSetRange(unsigned int range)


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

# Python extensions for wiringPi library functions.
cpdef wiringPiSetup():
    return wiringPiSetup()

cpdef wiringPiSetupSys():
    return wiringPiSetupSys()

cpdef wiringPiSetupGpio():
    return wiringPiSetupGpio()

cpdef wiringPiSetupPiFace():
    return wiringPiSetupPiFace()

cpdef _pinMode(int pin, int mode):
    pinMode(pin, mode)

cpdef _pullUpDnControl(int pin, int pud):
    pullUpDnControl(pin, pud)

cpdef _digitalWrite(int pin, int value):
    digitalWrite(pin, value)

cpdef _pwmWrite(int pin, int value):
    pwmWrite(pin, value)

cpdef _setPadDrive(int group, int value):
    setPadDrive(group, value)

cpdef _digitalRead(int pin):
    return digitalRead(pin)

cpdef _delayMicroseconds(unsigned int howLong):
    delayMicroseconds(howLong)

cpdef _pwmSetMode(int mode):
    pwmSetMode(mode)

cpdef _pwmSetRange(unsigned int range):
    pwmSetRange(range)
    
    

############################################

def demo():
    """
    Decode compressed data into image array.
    """

    print('hello!')
    val = wiringPiSetupGpio()
    print(val)

    val = digitalRead(17)
    print(val)
