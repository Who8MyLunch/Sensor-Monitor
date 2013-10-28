
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

def _pinMode(int pin, int mode):
    pinMode(pin, mode)

def _digitalRead(int pin):
    return digitalRead(pin)

def _digitalWrite(int pin, int value):
    digitalWrite(pin, value)

_LOW = LOW
_HIGH = HIGH
_MODE_PINS = MODE_PINS
_MODE_GPIO = MODE_GPIO
_INPUT = INPUT
_OUTPUT = OUTPUT
_PWM_OUTPUT = PWM_OUTPUT
_PUD_OFF = PUD_OFF
_PUD_DOWN = PUD_DOWN
_PUD_UP = PUD_UP


_GPIO_IS_SETUP = False

def _setup_gpio():
    """Do stuff to initialize.
    """
    if not globals()['_GPIO_IS_SETUP']:
        val = wiringPiSetupGpio()
        if val < 0:
            raise Exception('Problem seting up WiringPI.  Did you forget to run as root?')

        globals()['_GPIO_IS_SETUP'] = True


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

#################################################


@cython.boundscheck(False)
@cython.wraparound(False)
def read_raw(int pin_data, int num_data=4000, int delay=1):
    """
    Read raw data stream from sensor.
    num_data == number of data measurements to make.
    """

    # SetupGpio()

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


def compute_checksum(byte_1, byte_2, byte_3, byte_4, byte_5):
    """Compute checksum.  Return True or false.
    """
    val_sum = byte_1 + byte_2 + byte_3 + byte_4
    val_check = val_sum & 255

    if val_check == byte_5:
        return True
    else:
        return False


def bits_to_bytes(bits):
    """Assemble sequence of bits into valid byte data.  Test checksum.
    """
    if len(bits) != 40:
        raise ValueError('list of bits not equal to 40: %d' % len(bits))

    byte_1_str = ''
    for b in bits[0:8]:
        byte_1_str += str(b)
    byte_1 = np.int(byte_1_str, 2)

    byte_2_str = ''
    for b in bits[8:16]:
        byte_2_str += str(b)
    byte_2 = np.int(byte_2_str, 2)

    byte_3_str = ''
    for b in bits[16:24]:
        byte_3_str += str(b)
    byte_3 = np.int(byte_3_str, 2)

    byte_4_str = ''
    for b in bits[24:32]:
        byte_4_str += str(b)
    byte_4 = np.int(byte_4_str, 2)

    byte_5_str = ''
    for b in bits[32:40]:
        byte_5_str += str(b)
    byte_5 = np.int(byte_5_str, 2)

    # Test checksum.
    ok = compute_checksum(byte_1, byte_2, byte_3, byte_4, byte_5)

    # Done.
    return byte_1, byte_2, byte_3, byte_4, ok


def c2f(C):
    """Convert Celcius to Fahrenheit.
    """
    F = C * 9./5. + 32.
    return F


def f2c(F):
    """Convert Fahrenheit to Celcius.
    """
    C = (F - 32.) * 5./9.
    return C


def read_dht22_single(pin_data, delay=1):
    """
    Read temperature and humidity data from sensor.
    Just a single sample.  Return None if checksum fails or any other problem.
    """

    time.sleep(0.01)

    # Read some bits.
    first, bits = read_bits(pin_data, delay=delay)

    if first is None:
        msg = bits
        return None, msg

    if first != 1:
        msg = 'Fail first != 1'
        return None, msg

    # Convert recorded bits into data bytes.
    if len(bits) == 40:
        # Total number of bits is Ok.
        byte_1, byte_2, byte_3, byte_4, ok = bits_to_bytes(bits)

        if ok:
            # Checksum is OK.
            RH = float((np.left_shift(byte_1, 8) + byte_2) / 10.)
            Tc = float((np.left_shift(byte_3, 8) + byte_4) / 10.)

            # Convert Celcius to Fahrenheit.
            Tf = c2f(Tc)
        else:
            # Problem!
            msg = 'Fail checksum'
            RH, Tf = None, msg

    else:
        # Problem.
        msg = 'Fail len(bits) != 40 [%d]' % (len(bits))
        RH, Tf = None, msg

    # Done.
    return RH, Tf

#################################################

# Ensure that WiringPi's is properly setup for GPIO.  This should run during import.
_setup_gpio()
