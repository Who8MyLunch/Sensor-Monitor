
from __future__ import division, print_function, unicode_literals

import time
import numpy as np
import data_io as io

import dht22
import measure_timing

####################
# Helper functions.
def c2f(C):
    """
    Convert Celcius to Fahrenheit.
    """
    F = C * 9./5. + 32.
    return F

    
def f2c(F):
    """
    Convert Fahrenheit to Celcius.
    """
    C = (F - 32.) * 5./9.
    return C


##########################

def _read_dht22_single(pin_data, delay=1):
    """
    Read temperature and humidity data from sensor.
    """
    first, bits = dht22.read_bits(pin_data, delay=delay)

    if first != 1:
        msg = 'fail first != 1'
        return None, msg

    if len(bits) != 40:
        msg = 'fail len(bits) != 40 [%d]' % len(bits)
        return None, msg

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

    # Checksum.
    val_check = byte_1 + byte_2 + byte_3 + byte_4
    val_check = val_check & 255

    if val_check == byte_5:
        # All is OK.
        RH = (np.left_shift(byte_1, 8) + byte_2) / 10.
        Tc = (np.left_shift(byte_3, 8) + byte_4) / 10.
        
        Tf = c2f(Tc)
    else:
        # Data error.
        msg = 'Fail checksum.'
        RH, Tf = None, msg

    # Done.
    return RH, Tf


    
def monitor 



if __name__ == '__main__':

    # Read raw data.
    # print('\nreading raw')
    # data, info = dht22.read_raw(pin_data)
    # print('\nwriting to file')
    # f = 'sensor_data.npz'
    # io.write(f, data)


    delay = 2
    pin_data = 25

    dt = measure_timing.timing(pin=pin_data, time_poll=10)
    print('\nTiming: %.2f' % (dt*1000))


    # Read bits.
    pin_data = 23
    print('\nRead pin %d' % pin_data)
    RH, T = read_dht22(pin_data, delay=delay)
    if RH is None:
        msg = T
        print(msg)
    else:
        print('RH: %f' % RH)
        print('T: %f' % T)



    # Read bits.
    pin_data = 18
    print('\nRead pin %d' % pin_data)
    RH, T = read_dht22(pin_data, delay=delay)

    if RH is None:
        msg = T
        print(msg)
    else:
        print('RH: %f' % RH)
        print('T: %f' % T)

    print('\nDone')

