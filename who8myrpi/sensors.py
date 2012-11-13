
from __future__ import division, print_function, unicode_literals

import os
import time
import datetime

import numpy as np

import data_io as io
import data_cache as cache

# import gpio
import dht22
import measure_timing

####################
# Helper functions.
#
def c2f(C):
    """
    Convert Celcius to Fahrenheit.
    """
    F = C * 9./5. + 32.
    return F


def f2c(F):
    """
    Convert Fahrenheit to Celcius.
    """
    C = (F - 32.) * 5./9.
    return C


####################################

def compute_checksum(byte_1, byte_2, byte_3, byte_4, byte_5):
    """
    Compute checksum.
    Return True or false.
    """
    val_sum = byte_1 + byte_2 + byte_3 + byte_4
    val_check = val_sum & 255

    if val_check == byte_5:
        return True
    else:
        return False



def bits_to_bytes(bits):
    """
    Assemble sequence of bits into valid byte data.
    Test checksum.
    """
    if len(bits) != 40:
        raise ValueError('list of bits not equal to 40: %d' % len(bits))

    byte_1_str = ''
    for b in bits[0:8]:
        byte_1_str += str(b)
    byte_1 = np.int(byte_1_str, 2)

    byte_2_str = ''
    for b in bits[8:16]:
        byte_2_str += str(b)
    byte_2 = np.int(byte_2_str, 2)

    byte_3_str = ''
    for b in bits[16:24]:
        byte_3_str += str(b)
    byte_3 = np.int(byte_3_str, 2)

    byte_4_str = ''
    for b in bits[24:32]:
        byte_4_str += str(b)
    byte_4 = np.int(byte_4_str, 2)

    byte_5_str = ''
    for b in bits[32:40]:
        byte_5_str += str(b)
    byte_5 = np.int(byte_5_str, 2)

    # Test checksum.
    ok = compute_checksum(byte_1, byte_2, byte_3, byte_4, byte_5)

    # Done.
    return byte_1, byte_2, byte_3, byte_4, ok



def read_dht22_single(pin_data, delay=1):
    """
    Read temperature and humidity data from sensor.
    Just a single sample.  Return None if checksum fails or any other problem.
    """

    # Read some bits.
    first, bits = dht22.read_bits(pin_data, delay=delay)

    if first is None:
        msg = bits
        return None, msg

    if first != 1:
        msg = 'Fail first != 1'
        return None, msg

    # Convert recorded bits into data bytes.
    if len(bits) == 40:
        # Ok.
        byte_1, byte_2, byte_3, byte_4, ok = bits_to_bytes(bits)
        
    # elif len(bits) == 39:
        # # Special logic to attempt to recover from rare problem.
        # # Try a zero.
        # # bits_repaired = np.append(bits, 0)
        # bits_repaired = np.append(0, bits)
        # byte_1, byte_2, byte_3, byte_4, ok = bits_to_bytes(bits_repaired)
        # if not ok:
            # # Still not right.  Try a one.
            # # bits_repaired = np.append(bits, 1)
            # bits_repaired = np.append(1, bits)
            # byte_1, byte_2, byte_3, byte_4, ok = bits_to_bytes(bits_repaired)
        # if ok:
            # print('Repair worked!')
        # else:
            # print('Repair failed!')
    else:
        msg = 'Fail len(bits) != 40 [%d]' % (len(bits))
        return None, msg

    # Finish.
    if ok:
        # All is OK.
        RH = (np.left_shift(byte_1, 8) + byte_2) / 10.
        Tc = (np.left_shift(byte_3, 8) + byte_4) / 10.
    else:
        # Problem!
        msg = 'Fail checksum'
        RH, Tc = None, msg

    # Done.
    return RH, Tc


def set_status_led(status, pin_ok, pin_err):
    if status > 0:
        # Ok
        dht22._digitalWrite(pin_ok, 1)
        dht22._digitalWrite(pin_err, 0)
    elif status == 0:
        # Problem.
        dht22._digitalWrite(pin_ok, 0)
        dht22._digitalWrite(pin_err, 1)
    else:
        # Unknown.
        dht22._digitalWrite(pin_ok, 0)
        dht22._digitalWrite(pin_err, 0)
        
    # Done.
    
    
def read_dht22(pins_data, pin_ok, pin_err, recording_interval=60., delta_time_wait=2.1, ):
    """
    Read data from dht22 sensor.  Collect data over short time interval.  Return median value.
    Ignore any invalid data values.

    pins_data = integer or sequence of integers.
    recording_interval = recording time interval in seconds.
    delta_time_wait = time delay between attempts to read from sensors.  Must be at least 2 seconds.
    """

    if np.isscalar(pins_data):
        pins_data = [pins_data]

    if delta_time_wait < 2:
        raise ValueError('Invalid value for delta_time_wait: %s' % delta_time_wait)

    # Setup data containers.
    num_pin = len(pins_data)

    info_data = [None] * num_pin
    for k in range(num_pin):
        info_data[k] = {'pin': None,
                        'RH': [],
                        'Tc': [],
                        'time': []}

    # Main loop over data sampling time interval.
    time_start = time.time()
    time_run = 0.
    while time_run < recording_interval:
        set_status_led(-1, pin_ok, pin_err)
        time.sleep(delta_time_wait)
        
        # Loop over sensor pins.
        for k, pin in enumerate(pins_data):
            value = read_dht22_single(pin)

            if value[0] is None:
                set_status_led(0, pin_ok, pin_err)
                # Problem with sensor measurement.
                message = value[1]
                # print('pin %2d: problem: %s' % (pin, message))
            else:
                set_status_led(1, pin_ok, pin_err)
                time_now = time.time()
                time_run = time_now - time_start

                RH, Tc = value
                info_data[k]['pin'] = pin
                info_data[k]['RH'].append(RH)
                info_data[k]['Tc'].append(Tc)
                info_data[k]['time'].append(time_now)

    set_status_led(-1, pin_ok, pin_err)
    
    # Finish.
    eps = 1.e-5
    info_results = []
    for info_data_k in info_data:

        pin = info_data_k['pin']
        data_RH = np.asarray(info_data_k['RH'])
        data_Tc = np.asarray(info_data_k['Tc'])
        data_time = np.asarray(info_data_k['time'])

        data_Tf = c2f(data_Tc)

        info_sample = {'pin': pin,
                       'RH_avg': np.mean(data_RH),
                       'RH_std': np.std(data_RH),
                       'Tf_avg': np.mean(data_Tf),
                       'Tf_std': np.std(data_Tf),
                       'Samples': len(data_RH),
                       'Time': np.mean(data_time)}

        if info_sample['RH_std'] < eps:
            info_sample['RH_std'] = 0.0
            
        if info_sample['Tf_std'] < eps:
            info_sample['Tf_std'] = 0.0
            
        info_results.append(info_sample)

    # Average time stamp over all data observations.
    vals = [info_sample['Time'] for info_sample in info_results]
    time_avg = np.mean(vals)
    for info_sample in info_results:
        info_sample['Time'] = time_avg

    # Done.
    return info_results



def check_pin_connected(pin_data):
    """
    Run some tests to see if data pin appears to be connected to sensor.
    """
    first, bits = dht22.read_bits(pin_data, delay=delay)

    if first is None:
        return False
    else:
        return True


_header = ['pin', 'RH_avg', 'RH_std', 'Tf_avg', 'Tf_std', 'Samples', 'Time']
def write_record(name, info_results):
    """
    Save experiment data record to file.
    """
    
    t = info_results[0]['Time']    
    d = datetime.datetime.utcfromtimestamp(t)
    time_stamp = d.strftime('%Y-%m-%d-%H-%M-%S')
    fname = name + '=' + time_stamp + '.csv'

    path = 'data'
    f = os.path.join(path, fname)
    
    data = []
    for info_sample in info_results:
        line = [info_sample[k] for k in _header]
        data.append(line)

    io.write(f, data, header=_header)
    
    # Done.


def collect_data(pins_data, pin_ok, pin_err, name=None):
    """
    Record data for an experiment from multiple sensors.
    Save data to files.

    name: experiment name.
    """
    
    dht22.SetupGpio()
    
    # Configure LED status pins.
    if pin_ok is not None:
        dht22._pinMode(pin_ok, 1)
        
    if pin_err is not None:
        dht22._pinMode(pin_err, 1)
        
    if np.isscalar(pins_data):
        pins_data = [pins_data]

    if name is None:
        name = 'dht22'
        for p in pins_data:
            name += '-%02d' % p

    # Start recording data.
    print('Begin experiment: %s' % name)

    try:
        # Main processing loop.
        ok = True
        while ok:
            info_results = read_dht22(pins_data, pin_ok, pin_err)

            write_record(name, info_results)
            
            # print()
            # for info in info_results:
                # value = (info['pin'], info['Time'], info['Samples'], info['RH_avg'])
                # print('pin: %2d, time: %.1f  samples: %2d  RH_avg: %5.2f' % value)

    except KeyboardInterrupt:
        # End it all when user hits ctrl-c.
        print()
        print('End experiment: %s' % name)

    # Done.



if __name__ == '__main__':

    # Read raw data.
    # print('\nreading raw')
    # data, info = dht22.read_raw(pin_data)
    # print('\nwriting to file')
    # f = 'sensor_data.npz'
    # io.write(f, data)

    time_experiment = 5. * 60. * 60. # seconds.
    pins_data = [4, 17, 21, 22, 18, 23]

    pin_ok = 0
    pin_err = 1

    # Timing.
    dt = measure_timing.timing(pin=pins_data[0], time_poll=10)
    print('\nTiming: %.2f' % (dt*1000))

    # Read data over extended time period.
    print('\nRead from pins %s' % pins_data)
    
    collect_data(pins_data, pin_ok, pin_err)
    
    
    # time_start = time.time()
    # time_run = 0.
    # while time_run < time_experiment:
        # time_now = time.time()
        # time_run = time_now - time_start

        # info_results = read_dht22(pin_data, pin_ok, pin_err)

        # print()
        # for info in info_results:
            # value = (info['pin'], info['Time'], info['Samples'], info['RH_avg'])
            # print('pin: %2d, time: %.1f  samples: %2d  RH_avg: %5.2f' % value)

    print('\nDone')

    # Done.
