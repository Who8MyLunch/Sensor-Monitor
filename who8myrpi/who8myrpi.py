
from __future__ import division, print_function, unicode_literals

import os
import argparse

import data_io as io

import utility
import master_table
import upload
import sensors
import dht22

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

        # Update master config table with tableId for current data table.
        info_master = master_table.set(tableId)
        # print(info_master)

        # Run the uploader function.  Run until killed or exception.
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

#############################################33

def initialize(info_config):
    """
    Do all setup operations necesary to get ready prior to recording data.
    """
    
    # Config data.
    pins_data = info_config['pins_data']
    pin_ok = info_config['pin_ok']
    pin_err = info_config['pin_err']
    pin_power = info_config['pin_power']

    # Initialize GPIO.
    dht22.SetupGpio()

    # Power up the sensors.
    if pin_power is not None:
        dht22._pinMode(pin_power, dht22._OUTPUT)
        dht22._digitalWrite(pin_power, dht22._HIGH)
        time.sleep(5)

    # Configure status pins.
    if pin_ok is not None:
        dht22._pinMode(pin_ok, dht22._OUTPUT)
        dht22._digitalWrite(pin_ok, dht22._LOW)

    if pin_err is not None:
        dht22._pinMode(pin_err, dht22._OUTPUT)
        dht22._digitalWrite(pin_err, dht22._LOW)

    # Create data recording channels.
    channels, queue == sensors.start_channels(pins_data, pin_err=pin_err, pin_ok=pin_ok)
    ok = sensors.check_channels_ok(channels, verbose=True)

    if not ok:
        raise ValueError('Data channels not ready.')

    # Done.
    return channels, queue



def record_data(channels, queue):
    """
    Do the work to record data from sensors.
    """

    # Main processing loop.
    while True:
        # Record some data.

        # Upload data to online storage.

        # Repeat.


    # Finish.

    # Done.










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

    

def finalize(channels, info_config):
    """
    Do all operations necesary to shutdown.
    """

    # Stop recording.
    sensors.stop_channels(channels)

    # Turn off the sensors.
    if info_config['pin_power'] is not None:
        dht22._digitalWrite(info_config['pin_power'], dht22._LOW)

    # Done.


##################################################



def main():
    """
    This is the entry point for the main application.
    """

    #
    # Build and query the parser.
    #
    parser = argparse.ArgumentParser()
    # parser.add_argument('-U', '--upload', default=False, action='store_true',
                        # help='Upload sensor data to my Fusion Table.')
    # parser.add_argument('-R', '--record', default=False, action='store_true',
                        # help='Record data from DHT22 sensors.')
    parser.add_argument('-C', '--config_file', default=None,
                        help='Config file name.')

    # Parse command line input, do the work.
    args = parser.parse_args()

    # Config file.
    if args.config_file is None:
        args.config_file = 'config_data.yml'

    f = os.path.join(path_to_module(), args.config_file)
    info_config, meta = io.read(f)

    #
    # Do it.
    #
    try:
        channels, queue = initialize(info_config)
        
        # Timing, FYI.
        time.sleep(1)
        pin_timing = info_config['pins_data'][0]

        dt = sensors.measure_timing.timing(pin=pin_timing, time_poll=10)
        print('Timing: %.2f us' % (dt*1000))

        # Start recording data.
        print('Record from data pins: %s' % info_config['pins_data'])
        record_data(channels, queue)

    except KeyboardInterrupt:
        # Stop it all when user hits ctrl-C.
        print()
        print('User stop!')
    
    # Finish.
    finalize(channels, info_config)
    
    # Done.
    print('Done.')


if __name__ == '__main__':
    main()



