
from __future__ import division, print_function, unicode_literals

import data_io as io
import dht22

import numpy as np


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
    


def read_sensor():
    pin = 21
    delta_time = 0
    
    values = dht22.read(pin, delta_time)
    f = 'data.txt'
    np.savetxt(f, values)
    
    return values
    # Done.
    
    
    
            
if __name__ == '__main__':
    values = read_sensor()
    