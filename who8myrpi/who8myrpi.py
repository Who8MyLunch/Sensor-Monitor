
from __future__ import division, print_function, unicode_literals

import os
import argparse

import upload
import sensors


def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p

###############################3

def run_upload(experiment_name, path_data, path_credentials):
    """
    Do the work to upload to my Fusion Table.
    """

    max_allowed_resets = 5
    num_resets = 0
    keep_looping = True
    while keep_looping:
        # Setup Google API credentials.
        print('Acquire API credentials...')
        service, tableId = upload.acquire_api_service(experiment_name, path_credentials)

        print('Table ID: %s' % tableId)

        num_uploaded = upload.upload_data(service, tableId, path_data, status_interval=60*30)

        if num_uploaded >= 0:
            # Clean exit.
            keep_looping = False
        else:
            # Reset and try again.
            num_resets += 1

            if num_resets > max_allowed_resets:
                keep_looping = False
                raise Exception('Max number of resets exceeded.')
            else:
                keep_looping = True
                print()
                print('Reset API connection!')                
            
    # Done.


def run_record(experiment_name, path_data):
    """
    Do the work to record data from sensors.
    """
    # Pins.
    pins_data = [4, 17, 18, 21, 22, 23]
    pin_ok = 0
    pin_err = 1

    # Timing.
    dt = sensors.measure_timing.timing(pin=pins_data[0], time_poll=10)
    print('Timing: %.2f us' % (dt*1000))

    # Read data over extended time period.
    print('Data pins: %s' % pins_data)
    sensors.collect_data(pins_data, pin_ok, pin_err, path_data)

    print('End data recording')

    # Done.


#####################################

def main():
    """
    This is the main application.
    """
    path_data = os.path.join(path_to_module(), 'data')
    path_credentials = os.path.join(path_to_module(), 'credentials')

    experiment_name = 'Testing H | Six Sensors'

    # Build the parser.
    parser = argparse.ArgumentParser()
    parser.add_argument('-U', '--upload', default=False, action='store_true',
                        help='Upload sensor data to my Fusion Table.')
    parser.add_argument('-R', '--record', default=False, action='store_true',
                        help='Record data from DHT22 sensors.')

    # Parse command line input, do the work.
    args = parser.parse_args()

    if args.record:
        print('Record data: %s' % experiment_name)
        run_record(experiment_name, path_data)
    elif args.upload:
        print('Upload data: %s' % experiment_name)
        run_upload(experiment_name, path_data, path_credentials)
    else:
        print()
        print('Error!  Must supply command-line argument.')

    # Done.


if __name__ == '__main__':
    main()



