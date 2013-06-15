
from __future__ import division, print_function, unicode_literals

import time

import data_io as io
import gpio
import dht22
import sensors

import numpy as np

def blinking():
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

            
            
def read_sensor():
    pin = 4
    delay = 1
    

    values = sensors.read_dht22_single(pin, delay=delay)

    #f = 'data.txt'
    #np.savetxt(f, values)
    
    return values
    # Done.
    
    
    
            
if __name__ == '__main__':
    values = read_sensor()

    print(values)
    # blinking()
    