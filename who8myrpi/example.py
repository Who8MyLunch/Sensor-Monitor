
from __future__ import division, print_function, unicode_literals

import time

import gpio
import numpy as np

def work():
    """
    Just testing!
    """

    # Setup.
    pins_led = [18, 23, 24, 25]
    
    pin_switch_a = 17
    pin_switch_b = 4

    val = gpio.wiringPiSetupGpio()
    if val < 0:
        raise Exception('Problem seting up WiringPI.')

    # Configure GPIO pins.
    for pin in pins_led:
        gpio.pinMode(pin, gpio.OUTPUT)

    gpio.pinMode(pin_switch_a, gpio.INPUT)
    gpio.pinMode(pin_switch_b, gpio.INPUT)

    gpio.pullUpDnControl(pin_switch_a, gpio.PUD_DOWN)
    gpio.pullUpDnControl(pin_switch_b, gpio.PUD_DOWN)
    
    time_delta = 0.1
    
    # Main loop.
    flag = True
    while flag:
        time.sleep(time_delta)
        
        # Read switches.
        val_a = gpio.digitalRead(pin_switch_a)
        val_b = gpio.digitalRead(pin_switch_b)
        
        if val_a:
            time_delta *= 1.1
            print(time_delta)
        if val_b:
            time_delta *= 0.9
            print(time_delta)
            
        
            
        # Set LEDs.
        for pin in pins_led:
            value_rnd = np.random.random_integers(0, 1)
            gpio.digitalWrite(pin, value_rnd)
        
if __name__ == '__main__':
    work()
