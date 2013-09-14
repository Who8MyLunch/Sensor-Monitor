Who8MyRPi
=========

This repository contains Python code and Cython extension to interact with the RaspberryPi's GPIO lines.  This software repository devloped as I began experimenting with collecting data from small sensors using my new Raspberry Pi computer.  The core functionality for communication with the sensors via "bit banging" is handled by the Cython module dht22.pyx.  The module sensors.py handles the higher level functions for managing a given sensor over the runtime of the application.  Each sensor is controlled by an instance of the Channel class, itself subclassed from threading.Thread.  This class takes care of invalid data samples and historical outliers.  Aggregated results are push to a Queue where the main application framework waits for data updates.


Modules
-------

 - **blinking**: a simple example of turning LEDs on and off at random.  Also read from two switches to increase or decrease LED blink rate.

 - **measure_timing**: Cython-based extension I created to measure how fast I could  read/write from/to the GPIO pins.  Currently I see just under 1 microsecond.

 - **sensors**: Python module containing my high-level interface to various sensors.  Currently only support DHT22 temperature & humity sensor.  I have future plans for barometric pressure and one more type of humidity sensor.

 - **dht22**: Cython module for direct fast interfacing to DHT22 temperature & humidy sensors.  It was necesary to write this in Cython instead of Python because of requirements for relative fast sample rates reading from the sensor.

 - **_gpio**: Cython-based wrapper for WiringPi.  Initially inspired by WirinPi-Python, but that was based on Swig and not easy for me to modify.

 - **gpio**: Python wrapper around _gpio.  My two-level wrapper system is probably more complicated than it needs to be...

Requirements
------------

 - Cython
 - Numpy
