
from __future__ import division, print_function, unicode_literals

import os
import argparse

import data_io as io

import utility
import master_table
import upload
import sensors

###############################
# Helpers.
def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p

###############################


def run_upload(info_config):
    """
    Do the work to upload to my Fusion Table.
    """

    # Config.
    experiment_name = info_config['experiment_name']

    path_credentials = os.path.join(path_to_module(), 'credentials')
    path_data = os.path.join(path_to_module(), 'data')
    
    folder_experiment = utility.valid_filename(experiment_name)
    path_data_work = os.path.join(path_data, folder_experiment)

    
    max_allowed_resets = 1000
    num_resets = 0
    keep_looping = True
    
    while keep_looping:
        # Setup Google API credentials.
        service, tableId = upload.connect_table(experiment_name, path_credentials)

        print('Table ID: %s' % tableId)

        1/0
        num_uploaded = upload.upload_data(service, tableId, path_data_work)

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


    
def run_record(info_config):
    """
    Do the work to record data from sensors.
    """

    # Config.
    experiment_name = info_config['experiment_name']
    
    path_data = os.path.join(path_to_module(), 'data')

    pins_data = info_config['pins_data']
    pin_ok = info_config['pin_ok']
    pin_err = info_config['pin_err']
    pin_power = info_config['pin_power']

    power_cycle_interval = info_config['power_cycle_interval']    
    
    # Timing, FYI.
    dt = sensors.measure_timing.timing(pin=pins_data[0], time_poll=10)
    print('Timing: %.2f us' % (dt*1000))

    # Read data over extended time period.
    print('Data pins: %s' % pins_data)
    
    folder_experiment = utility.valid_filename(experiment_name)
    path_data_work = os.path.join(path_data, folder_experiment)
    
    print('Begin data recording')
    sensors.collect_data(pins_data, path_data_work, 
                         pin_ok=pin_ok,
                         pin_err=pin_err,
                         pin_power=pin_power,
                         power_cycle_interval=power_cycle_interval)

    print('End data recording')

    # Done.


#####################################

    
    
def main():
    """
    This is the main application.
    """

    # Build the parser.
    parser = argparse.ArgumentParser()
    parser.add_argument('-U', '--upload', default=False, action='store_true',
                        help='Upload sensor data to my Fusion Table.')
    parser.add_argument('-R', '--record', default=False, action='store_true',
                        help='Record data from DHT22 sensors.')
    parser.add_argument('-C', '--config_file', default=None,
                        help='Config file name.')

    # Parse command line input, do the work.
    args = parser.parse_args()

    # Config file.
    if args.config_file is None:
        args.config_file = 'config_data.yml'
        
    f = os.path.join(path_to_module(), args.config_file)
    info_config, meta = io.read(f)
    
    if args.record:
        run_record(info_config)
    elif args.upload:
        run_upload(info_config)
    else:
        print()
        print('Error!  Must supply command-line argument.')

    # Done.


if __name__ == '__main__':
    main()



