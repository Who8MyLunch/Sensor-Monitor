
from __future__ import division, print_function, unicode_literals

import numpy as np
import data_io as io

import dht22

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

def read_sensor():
    pin_data = 21
    raw = True
    
    values = dht22.read(pin_data, raw=raw)
    # first, signal, tail = values
    # f = 'sensor_data.npz'
    # io.write(f, values)
    
    return values
    # Done.
    
    
    
if __name__ == '__main__':

    # first, signal, tail = read_sensor()
    # H = signal[:16]
    # T = signal[16:32]
    # check = signal[32:]
    
    print('\nreading')
    
    pin_data = 21
    num_data = 25000
    delay = 1
    
    data = dht22.read_raw(pin_data)

    print('\nwriting to file')
    
    f = 'sensor_data.npz'
    io.write(f, data)
    
    print('\ndone')
    