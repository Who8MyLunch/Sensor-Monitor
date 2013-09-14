
from __future__ import division, print_function, unicode_literals

import os
import argparse
import time

import numpy as np
import data_io as io

import utility
import master_table
import upload
import sensors
import dht22

import who8mygoogle

###############################

def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p

###############################


def initialize_sensors(info_config):
    """
    Do all setup operations necesary to get ready prior to recording data.
    """

    # Config data.
    pins_data = info_config['pins_data']
    #pins_data = pins_data.split(',')
    #pins_data = [int(pin) for pin in pins_data]

    pin_ok = int(info_config['pin_ok'])
    pin_err = int(info_config['pin_error'])
    pin_power = int(info_config['pin_power'])

    # Initialize GPIO.
    dht22.SetupGpio()

    # Power up the sensors.
    if pin_power:
        dht22._pinMode(pin_power, dht22._OUTPUT)
        dht22._digitalWrite(pin_power, dht22._HIGH)
        time.sleep(5)

    # Configure status pins.
    if pin_ok:
        dht22._pinMode(pin_ok, dht22._OUTPUT)
        dht22._digitalWrite(pin_ok, dht22._LOW)

    if pin_err:
        dht22._pinMode(pin_err, dht22._OUTPUT)
        dht22._digitalWrite(pin_err, dht22._LOW)

    # Create data recording channels.
    channels, queue = sensors.start_channels(pins_data, pin_err=pin_err, pin_ok=pin_ok)

    ok = sensors.check_channels_ok(channels, verbose=True)

    if not ok:
        raise ValueError('Data channels not ready.')

    # Done.
    return channels, queue



def initialize_upload(info_config):
    """
    Prepare Fusion Table service.
    """
    path_credentials = os.path.join(path_to_module(), 'credentials')

    # Setup Google API credentials.
    service, tableId = upload.connect_table(info_config['experiment_name'], path_credentials)
    print('Initialized, Data Table ID: %s' % tableId)

    # Done.
    return service, tableId



def record_data(channels, queue, service, tableId, info_config):
    """
    Do the work to record data from sensors.
    """

    power_cycle_interval = 10*60  # seconds

    # Setup.
    source = sensors.data_collector(queue)        # data producer / generator
    sink = upload.data_uploader(service, tableId) # consumer coroutine

    # Main processing loop.
    time_power_zero = time.time()
    for samples in source:
        try:
            # Pass the data along to the uploader.
            sink.send(samples)

            # Pretty status message.
            t = samples[0]['seconds']
            fmt = '%Y-%m-%d %H-%M-%S'
            time_stamp = utility.pretty_timestamp(t, fmt)
            print('samples:%3d [%s]' % (len(samples), time_stamp) )

            # Do a power cycle?
            if time.time() - time_power_zero > power_cycle_interval:
                print('Power cycle')
                power_cycle(channels, info_config)
                time_power_zero = time.time()

        except who8mygoogle.errors.Who8MyGoogleError as e:
            print()
            print('Error: %s' % e.message)
            break

        except KeyboardInterrupt:
            print()
            print('User stop!')
            break

    # Finish.
    sink.close()

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


def power_cycle(channels, info_config, time_off=None):
    """
    Power cycle all conected sensors.
    """
    if time_off is None:
        time_off = 30

    if info_config['pin_power'] is None:
        # Nothing to do.
        pass
    else:
        # Do it.
        sensors.pause_channels(channels)

        time.sleep(0.01)
        dht22._digitalWrite(info_config['pin_power'], dht22._LOW)

        time.sleep(time_off)

        dht22._digitalWrite(info_config['pin_power'], dht22._HIGH)
        time.sleep(0.01)

        sensors.unpause_channels(channels)

    # Done.

##################################################

# @coroutine
# def data_uploader(info_config):
    # """
    # Do the work to upload to my Fusion Table.
    # """
    # # Config.
    # experiment_name = info_config['experiment_name']
    # path_credentials = os.path.join(path_to_module(), 'credentials')
    # max_allowed_resets = 1000
    # num_resets = 0
    # # Setup Google API credentials.
    # service, tableId = upload.connect_table(experiment_name, path_credentials)
    # # print('Table ID: %s' % tableId)
    # # Update master config table with tableId for current data table.
    # info_master = master_table.set(tableId)
    # # print(info_master)
        # # Run the uploader function.  Run until killed or exception.
        # num_uploaded = upload.upload_data(service, tableId, path_data_work)
        # if num_uploaded >= 0:
            # # Clean exit.
            # keep_looping = False
        # else:
            # # Reset and try again.
            # num_resets += 1
            # if num_resets > max_allowed_resets:
                # keep_looping = False
                # raise Exception('Max number of resets exceeded.')
            # else:
                # keep_looping = True
                # print()
                # print('Reset API connection!')
    # # Done.


##################################################

def main():
    """
    This is the entry point for the application.
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
    info_master, meta = io.read(f)

    #
    # Do it.
    #
    try:
        # Retrieve config data from master table.
        print('Retrieve config data')
        info_config = master_table.get(info_master)

        # Convert some string values to integers.
        pins_data = info_config['pins_data']
        pins_data = pins_data.split(',')
        pins_data = [int(pin) for pin in pins_data]

        info_config['pins_data'] = pins_data

        info_config['pin_ok'] = int(info_config['pin_ok'])
        info_config['pin_err'] = int(info_config['pin_error'])
        info_config['pin_power'] = int(info_config['pin_power'])

        # Initialize stuff.
        print('Initialize sensors')
        channels, queue = initialize_sensors(info_config)

        print('Initialize upload')
        service, tableId = initialize_upload(info_config)

        # Start recording data.
        print('Begin recording: %s' % info_config['pins_data'])
        record_data(channels, queue, service, tableId, info_config)

    except KeyboardInterrupt:
        # Stop it all when user hits ctrl-C.
        print()
        print('Main: User stop!')

    # Finish.
    print('Stop recording')
    finalize(channels, info_config)

    # Done.
    print('Done.')


if __name__ == '__main__':
    main()



