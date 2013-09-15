
from __future__ import division, print_function, unicode_literals

import os
import argparse
import time

import numpy as np
import data_io as io

import dht22
import sensors
import utility
import blinker
import upload
import master_table

import who8mygoogle.fusion_tables as fusion_tables

#################################################

def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p

#################################################


def initialize_sensors(info_config):
    """
    Do all setup operations necesary to get ready prior to recording data.
    """

    # Config data.
    pins_data = info_config['pins_data']

    pin_power = int(info_config['pin_power'])

    # Initialize GPIO.
    dht22.SetupGpio()

    # Power up the sensors.
    if pin_power:
        dht22._pinMode(pin_power, dht22._OUTPUT)
        dht22._digitalWrite(pin_power, True)
        time.sleep(5)

    # Create data recording channels.
    channels, queue = sensors.start_channels(pins_data)

    ok = sensors.check_channels_ok(channels, verbose=True)

    if not ok:
        sensors.stop_channels(channels)
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

    power_cycle_interval = 5*60  # seconds

    # Status LED.
    pin_ok = int(info_config['pin_ok'])
    pin_upload = int(info_config['pin_err'])

    blink_sensors = blinker.Blinker(pin_ok)

    # Setup.
    source = sensors.data_collector(queue)                    # data producer / generator
    sink = upload.data_uploader(service, tableId, pin_upload) # consumer coroutine

    # Main processing loop.
    time_power_zero = time.time()
    for samples in source:
        try:
            # Pass the data along to the uploader.
            blink_sensors.frequency = 0

            sink.send(samples)

            blink_sensors.frequency = len(samples)

            # Pretty status message.
            t = samples[0]['seconds']
            fmt = '%Y-%m-%d %H-%M-%S'
            time_stamp = utility.pretty_timestamp(t, fmt)
            print('samples:%3d [%s]' % (len(samples), time_stamp) )

            # Do a power cycle?
            if time.time() - time_power_zero > power_cycle_interval:
                print('Power cycle')
                blink_sensors.frequency = 0.2

                power_cycle(channels, info_config)
                time_power_zero = time.time()

                blink_sensors.frequency = 0

        except fusion_tables.errors.Who8MyGoogleError as e:
            print()
            print('Error: %s' % e.message)
            break

        except KeyboardInterrupt:
            print()
            print('User stop!')
            break

        except Exception as e:
            # More gentle end for unknown exception.
            print(e)
            blink_sensors.stop()
            sink.close()

            raise e

    # Finish.
    blink_sensors.stop()
    sink.close()

    # Done.



def finalize(channels, info_config):
    """
    Do all operations necesary to shutdown.
    """

    # Stop recording.
    if channels:
        sensors.stop_channels(channels)

    # Turn off the sensors.
    if info_config:
        if info_config['pin_power']:
            print('pin_power off')
            dht22._digitalWrite(info_config['pin_power'], False)

    # Done.

##################################################


def power_cycle(channels, info_config, time_off=30):
    """
    Power cycle all conected sensors.

    time_off: sleep time in seconds.
    """

    if not info_config['pin_power']:
        # Nothing to do.
        pass
    else:
        # Do it.
        sensors.pause_channels(channels)

        time.sleep(0.01)
        dht22._digitalWrite(info_config['pin_power'], False)

        time.sleep(time_off)

        dht22._digitalWrite(info_config['pin_power'], True)
        time.sleep(0.01)

        sensors.unpause_channels(channels)

    # Done.

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
    if not args.config_file:
        args.config_file = 'config_data.yml'

    f = os.path.join(path_to_module(), args.config_file)
    info_master, meta = io.read(f)

    #
    # Do it.
    #
    channels = None
    info_config = None
    try:
        # Get config data from master table.
        print('Fetch master table config data')
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

        print('Initialize upload data API')
        service, tableId = initialize_upload(info_config)

        # Start recording data.
        print('Begin recording: %s' % info_config['pins_data'])
        record_data(channels, queue, service, tableId, info_config)

    except KeyboardInterrupt:
        # Stop it all when user hits ctrl-C.
        print()
        print('Main: User stop!')

    # except Exception as e:
    #     channels = None
    #     print(e)

    # Finish.
    print('Stop recording')
    finalize(channels, info_config)

    # Done.
    print('Done.')


if __name__ == '__main__':
    main()



