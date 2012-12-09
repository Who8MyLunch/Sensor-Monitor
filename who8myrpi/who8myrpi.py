
from __future__ import division, print_function, unicode_literals

import os
import argparse
import string

import upload
import sensors


def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p

###############################

def run_upload(table_name, path_data, path_credentials):
    """
    Do the work to upload to my Fusion Table.
    """

    print('Uploading data: %s' % table_name)
    
    max_allowed_resets = 1000
    num_resets = 0
    keep_looping = True
    while keep_looping:
        # Setup Google API credentials.
        service, tableId = upload.connect_table(table_name, path_credentials)

        print('Table ID: %s' % tableId)

        folder_experiment = valid_filename(table_name)
        path_data_work = os.path.join(path_data, folder_experiment)
        num_uploaded = upload.upload_data(service, tableId, path_data_work, status_interval=60*30)

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


def run_record(table_name, path_data):
    """
    Do the work to record data from sensors.
    """
    # Pins.
    pins_data = [4, 17, 21, 18, 23, 24, 25]
    # pins_data = [4, 17, 18, 23]
    pin_ok = 7
    pin_err = 8
    pin_power = 22

    power_cycle_interval = 60*10
    
    # Timing.
    dt = sensors.measure_timing.timing(pin=pins_data[0], time_poll=10)
    print('Timing: %.2f us' % (dt*1000))

    # Read data over extended time period.
    print('Data pins: %s' % pins_data)
    
    folder_experiment = valid_filename(table_name)
    path_data_work = os.path.join(path_data, folder_experiment)
    
    sensors.collect_data(pins_data, path_data_work, 
                         pin_ok=pin_ok,
                         pin_err=pin_err,
                         pin_power=pin_power,
                         power_cycle_interval=power_cycle_interval)

    print('End data recording')

    # Done.


#####################################

def valid_filename(fname_in):
    """
    Take a string and return a valid filename constructed from the string.
    Uses a whitelist approach: any characters not present in valid_chars are
    removed. Also spaces are replaced with underscores.

    Note: this method may produce invalid filenames such as ``, `.` or `..`
    When I use this method I prepend a date string like '2009_01_15_19_46_32_'
    and append a file extension like '.txt', so I avoid the potential of using
    an invalid filename.
    """
    valid_chars = '-_.() %s%s' % (string.ascii_letters, string.digits)

    fname_out = ''.join(c for c in fname_in if c in valid_chars)
    # fname_out = fname_out.replace(' ','_') # don't like spaces in filenames.

    # Done.
    return fname_out

    
    
def main():
    """
    This is the main application.
    """
    path_data = os.path.join(path_to_module(), 'data')
    path_credentials = os.path.join(path_to_module(), 'credentials')

    experiment_name = 'Testing I - One Sensor'

    # Build the parser.
    parser = argparse.ArgumentParser()
    parser.add_argument('-U', '--upload', default=False, action='store_true',
                        help='Upload sensor data to my Fusion Table.')
    parser.add_argument('-R', '--record', default=False, action='store_true',
                        help='Record data from DHT22 sensors.')

    # Parse command line input, do the work.
    args = parser.parse_args()

    if args.record:
        run_record(experiment_name, path_data)
    elif args.upload:
        run_upload(experiment_name, path_data, path_credentials)
    else:
        print()
        print('Error!  Must supply command-line argument.')

    # Done.


if __name__ == '__main__':
    main()



