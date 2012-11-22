
from __future__ import division, print_function, unicode_literals

import os
import argparse

import upload
import sensors


def run_upload():
    """
    Do the work to upload to my Fusion Table.
    """
    pass
    
    
def run_record():
    """
    Do the work to record data from sensors.
    """
    
    pins_data = [4, 17, 21, 22, 18, 23]

    pin_ok = 0
    pin_err = 1

    # Timing.
    dt = measure_timing.timing(pin=pins_data[0], time_poll=10)
    print('\nTiming: %.2f us' % (dt*1000))

    # Read data over extended time period.
    print('\nReading from pins: %s' % pins_data)

    sensors.collect_data(pins_data, pin_ok, pin_err)

    print('End data recording')
    
    # Done.
    
    

def main():
    """
    This is the main application.
    """

    # Build the parser.
    parser = argparse.ArgumentParser()
    parser.add_argument('-U', '--upload', default=False, action='store_true', help='Upload sensor data to my Fusion Table.')
    parser.add_argument('-R', '--record', default=False, action='store_true', help='Record data from DHT22 sensors.')

    # Parse command line input, do the work.
    args = parser.parse_args()
    
    print(args)
    
    if args.upload:
        run_upload()
    elif args.record:
        run_record()
    else:
        print()
        print('Error!  Must supply command-line argument.')
        
    # Done.


if __name__ == '__main__':
    main()

    
    
