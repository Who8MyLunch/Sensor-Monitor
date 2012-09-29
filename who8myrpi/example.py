
from __future__ import division, print_function, unicode_literals


import gpio
import numpy as np

def work():
    """
    Just testing!
    """

    # Setup.
    pins_lid = [18, 23, 24, 25]
    
    pin_switch_a = 4
    pin_switch_b = 4

    val = gpio.wiringPiSetupGpio()
    if val < 0:
        raise Exception('Problem seting up WiringPI.')

    for pin in pins_lid:
        gpio.pinMode(pin, gpio.OUTPUT)


    # Main loop.
    flag = True
    while flag:
        pin_rnd = 


if __name__ == '__main__':
    work()
