
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

#######################################


cdef int send_start(int pin_data) nogil:
    """
    Send start signal to sensor.

    The calling program must have already initialized the GPIO system by
    calling val = wiringPiSetupGpio().
    """

    # Set pin to output mode.
    # Set pin low.
    # Manual indicates must stay low for 1 - 10 ms.
    # Wait 10 milliseconds, long enough for sensor to see start signal.
    pinMode(pin_data, OUTPUT)
    digitalWrite(pin_data, LOW)
    delayMicroseconds(10*1000)

    # Set pin high to end start signal.  Indicate ready to receive data from sensor.
    # Can wait 20 - 40 microseconds before receiving response back from sensor.
    digitalWrite(pin_data, HIGH)
    # delayMicroseconds(1)

    # Switch pin back to input so we can read results from it in the next step.
    pinMode(pin_data, INPUT)

    # Done.
    return 0

#########################
    
@cython.boundscheck(False)
@cython.wraparound(False)
def read_raw(int pin_data, int num_data=4000, int delay=1):
    """
    Read raw data stream from sensor.
    num_data == number of data measurements to make.
    """

    val = wiringPiSetupGpio()
    if val < 0:
        raise Exception('Problem seting up WiringPI.')

    # Setup.
    data_signal = np.zeros(num_data, dtype=np.int)
    cdef int [:] data_signal_view = data_signal

    cdef int count = 0
    cdef int value_sensor = 0

    cdef int time_stop = 0
    cdef int time_start = millis()

    # Send start signal to the sensor.
    send_start(pin_data)

    # Main loop reading from sensor.
    with nogil:
        while count < num_data:
            delayMicroseconds(delay)
            
            value_sensor = digitalRead(pin_data)

            data_signal_view[count] = value_sensor

            count += 1


    # Finish.
    time_stop = millis()
    cdef float sample_time = float(time_stop - time_start) / float(count) * 1000.

    print('')
    print('count: %s' % count)
    print('sample_time: %s (microseconds)' % sample_time)
    print('time_start: %s' % time_start)
    print('time_stop:  %s' % time_stop)

    data_signal = data_signal[:count]

    if np.min(data_signal) == 1:
        print('Problem reading data from sensor on pin %d.  All data == 1' % pin_data)

    # Finish.
    info = {'sample_time': sample_time,
            'count': count}
            
    # Done.
    return data_signal, info

###########

cdef int read_single_bit(int pin_data, int delay) nogil:
    """
    Number of ticks that signal stays down.
    If timeout then return -1.
    """
    cdef int count_timeout = 200000
    cdef int count_wait = 0
    cdef int count_low = 0
    cdef int count_high = 0
    cdef int bit_value = 0
    cdef int diff = 0

    delayMicroseconds(delay)
    
    # While not ready.
    while digitalRead(pin_data) == HIGH:
        delayMicroseconds(delay)
        count_wait += 1
        if count_wait >= count_timeout:
            return -1

    # While LOW, indicates new signal bit.
    while digitalRead(pin_data) == LOW:
        delayMicroseconds(delay)
        count_low += 1
        if count_low >= count_timeout:
            return -2

    # While HIGH, duration of HIGH indicates bit value, 0 or 1.
    while digitalRead(pin_data) == HIGH:
        delayMicroseconds(delay)
        count_high += 1
        if count_high >= count_timeout:
            return -3

    # Determine signal value.
    diff = count_high - count_low

    if diff < 0:
        bit_value = 0
    else:
        bit_value = 1

    # Done.
    return bit_value



@cython.boundscheck(False)
@cython.wraparound(False)
def read_bits(int pin_data, int delay=1):
    """
    Read data from DHT22 sensor.
    delay = wait time between polling sensor, microseconds.
    """

    val = wiringPiSetupGpio()
    if val < 0:
        raise Exception('Problem seting up WiringPI.')

    # Storage.
    cdef int num_data = 41
    data = np.zeros(num_data, dtype=np.int)
    cdef int [:] data_view = data

    cdef int count = 0
    cdef int bit = 0

    with nogil:
        # Send start signal to the sensor.
        send_start(pin_data)
    
        # Read interpreted data bits.
        while count <= num_data:
            bit = read_single_bit(pin_data, delay)
            if bit < 0:
                # Problem reading bit value, exit loop.
                break

            data_view[count] = bit
            count += 1

    if count == 0:
        # raise Exception('Problem reading data from sensor.  Count == 0.  pin_data: %d, bit: %d' % (pin_data, bit) )
        msg = 'Problem reading data from sensor.  count: 0, pin: %d, bit: %d' % (pin_data, bit)
        return None, msg
        
    # Limit to just the data bits recorded.
    data = data[:count]
    first = data[0]
    bits = data[1:]

    # Done.
    return first, bits

