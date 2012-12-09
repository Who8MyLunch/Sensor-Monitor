
from __future__ import division, print_function, unicode_literals

import os
import time
import datetime
import string
import threading
import Queue

import numpy as np

import data_io as io
# import data_cache as cache

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


def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p


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

    time.sleep(0.01)

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



def set_status_led(status, pin_ok=None, pin_err=None):
    if not (pin_ok == None or pin_err == None):
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
    else:
        # Do nothing.
        pass

    # Done.



def read_dht22(pins_data, recording_interval=60, delta_time_wait=2.1,
               pin_ok=None, pin_err=None, pin_power=None):
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
            time_now = time.time()
            time_run = time_now - time_start

            if value[0] is None:
                # Problem with sensor measurement.
                set_status_led(0, pin_ok, pin_err)
                message = value[1]
                RH, Tc = -1, -1

                # print('problem with pin: %d' % pin)
                # print(message)
            else:
                # Measurement OK.
                set_status_led(1, pin_ok, pin_err)
                RH, Tc = value
                # print('ok', RH, Tc)

            info_data[k]['pin'] = pin
            info_data[k]['RH'].append(RH)
            info_data[k]['Tc'].append(Tc)
            info_data[k]['time'].append(time_now)

    # print(info_data)
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

        whr_valid = np.where(data_RH > 0)
        num_valid = len(whr_valid[0])

        if num_valid > 0:
            RH_avg = np.mean(data_RH[whr_valid])
            RH_std = np.std(data_RH[whr_valid])
            Tf_avg = np.mean(data_Tf[whr_valid])
            Tf_std = np.std(data_Tf[whr_valid])
            Samples = len(data_RH[whr_valid])
            Time = np.mean(data_time[whr_valid])

            RH_avg = np.round(RH_avg, 3)
            RH_std = np.round(RH_std, 3)
            Tf_avg = np.round(Tf_avg, 3)
            Tf_std = np.round(Tf_std, 3)
            Time = np.round(Time, 2)

            info_sample = {'pin':    pin,
                           'RH_avg': RH_avg,
                           'RH_std': RH_std,
                           'Tf_avg': Tf_avg,
                           'Tf_std': Tf_std,
                           'Samples': Samples,
                           'Time':   Time}

            if info_sample['RH_std'] < eps:
                info_sample['RH_std'] = 0.0

            if info_sample['Tf_std'] < eps:
                info_sample['Tf_std'] = 0.0

            info_results.append(info_sample)
        else:
            # Problem??
            print('No valid samples for pin %d' % pin)


    # Average time stamp over all data observations.
    vals = [info_sample['Time'] for info_sample in info_results]

    time_avg = np.round(np.mean(vals), 3)
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
def write_record(sensor_name, info_results, path_data=None):
    """
    Save experiment data record to file.
    """
    if path_data is None:
        path_base = os.path.curdir
        folder_data = 'data'
        path_data = os.path.join(path_base, folder_data)

    if not os.path.isdir(path_data):
        os.mkdir(path_data)

    t = info_results[0]['Time']
    d = datetime.datetime.utcfromtimestamp(t)
    time_stamp = d.strftime('%Y-%m-%d - %H-%M-%S')

    folder_day = d.strftime('%Y-%m-%d')
    path_day = os.path.join(path_data, folder_day)

    if not os.path.isdir(path_day):
        os.mkdir(path_day)

    # Output to file.
    fname = sensor_name + ' - ' + time_stamp + '.csv'

    f = os.path.join(path_day, fname)

    data = []
    for info_sample in info_results:
        line = [info_sample[k] for k in _header]
        data.append(line)

    io.write(f, data, header=_header)

    # Done.


def build_summary(info_results, info_summary=None, pins_data=None):
    """
    Summary of collected data.
    """
    if info_summary is None:
        info_summary = {}
        if pins_data is not None:
            for p in pins_data:
                info_summary[p] = 0

    for info_sample in info_results:
        p = info_sample['pin']
        n = info_sample['Samples']

        if not p in info_summary:
            info_summary[p] = 0

        info_summary[p] += n

    # Done.
    return info_summary



def pretty_status(time_now, info_summary):
    """
    Display pretty status update.
    """
    d = datetime.datetime.utcfromtimestamp(time_now)
    time_stamp = d.strftime('%Y-%m-%d %H:%M:%S')

    pin_count_str = ''
    for p, n in info_summary.items():
        s = '%3d' % (n)
        pin_count_str += s + ' '

    msg = '%s || %s' % (time_stamp, pin_count_str)
    print(msg)

    # Done.


def reset_power(pin_power=None):
    """
    Power cycle the sensors.
    """
    if pin_power is None:
        pass
    else:
        # Do it.
        dht22._digitalWrite(pin_power, 0)
        time.sleep(30)
        dht22._digitalWrite(pin_power, 1)

    # Done.



def collect_data(pins_data, path_data,
                 status_interval=60*10,
                 delta_time_wait=5,
                 recording_interval=60,
                 power_cycle_interval=60*60,
                 pin_ok=None, pin_err=None, pin_power=None):
    """
    Record data for an experiment from multiple sensors.
    Save data to files.

    status_interval = seconds between status updates.
    """

    sensor_name = 'dht22'
    dht22.SetupGpio()

    # Configure LED status pins.
    if pin_ok is not None:
        dht22._pinMode(pin_ok, 1)

    if pin_err is not None:
        dht22._pinMode(pin_err, 1)

    if pin_power is not None:
        dht22._pinMode(pin_power, 1)
        dht22._digitalWrite(pin_power, 1)
        time.sleep(5)

    if np.isscalar(pins_data):
        pins_data = [pins_data]

    # Main processing loop.
    time_status_zero = time.time()
    time_power_zero = time.time()

    info_summary = None
    try:
        ok = True
        while ok:
            # Collect data over specified recording interval.
            info_results = read_dht22(pins_data,
                                      recording_interval=recording_interval,
                                      delta_time_wait=delta_time_wait,
                                      pin_ok=pin_ok, pin_err=pin_err)

            # Save data to file.
            write_record(sensor_name, info_results, path_data=path_data)
            info_summary = build_summary(info_results, info_summary, pins_data=pins_data)

            # Time-based checks.
            time_now = time.time()

            # Status display.
            if time_now - time_status_zero > status_interval:
                pretty_status(time_now, info_summary)

                time_status_zero = time_now
                info_summary = None


            # Power cycle the sensors.
            if time_now - time_power_zero > power_cycle_interval:
                reset_power(pin_power)
                time_power_zero = time_now


    except KeyboardInterrupt:
        # End it all when user hits ctrl-C.
        if pin_ok is not None:
            dht22._digitalWrite(pin_ok, 0)
        if pin_err is not None:
            dht22._digitalWrite(pin_err, 0)

        if pin_power is not None:
            dht22._digitalWrite(pin_power, 0)


        print()
        print('User stop!')

    # Done.



_time_wait_default = 2.5
_time_history_default = 10*60

class Channel(threading.Thread):
    def __init__(self, pin, time_wait=None, time_history=None, *args, **kwargs):
        """
        Record data in Thread from specified sensor pin.

        time_wait: seconds between polling sensor
        time_history: seconds of historical data remembered
        """

        threading.Thread.__init__(self, *args, **kwargs)

        if time_wait is None:
            time_wait = _time_wait_default

        if time_history is None:
            time_history = _time_history_default

        self.pin = pin
        self.time_wait = time_wait
        self.time_history = time_history
        self.data_history = []

        self._alive = False
        self.queue = Queue.Queue(maxsize=100)

        # Done.



    def run(self):
        """
        This is where the work happens.
        """
        self._alive = True
        while self._alive:
            RH, Tc = read_dht22_single(pin_data, delay=1)
            time_zero = time.clock()

            if RH is None:
                # Reading is not valid.
                pass
            else:
                # Reading is good.  Store it.
                Tf = c2f(Tc)
                time_stamp = time.time()

                info = {'RH': RH,
                        'Tf': Tf,
                        'time_stamp': time_stamp}

                self.add_data(info)

            # Wait a bit.
            time_delta = self.time_wait - (time.clock() - time_zero)
            time.sleep(time_delta)

            # Repeat.


    def stop(self):
        """
        Tell thread to stop running.
        """
        self._alive = False


    def add_data(self, info):
        """
        Add new data point.
        """
        self.data_history.append(info)
        num_removed = self.adjust_history()

        


        # Done.


    def adjust_history(self):
        """
        Remove data from history if older than time window.
        """

        # Times.
        time_stamp_now = time.time()

        # Look for data that's too old.
        list_too_old = []
        for d in self.data_history:
            delta = time_stamp_now - d['time_stamp']

            if delta > self.time_history:
                list_too_old.append(d)

        # Remove data older than history window.
        for d in list_too_old:
            self.data_history.remove(d)

        # Done.
        return len(list_too_old)
        

    def check_values(self, info_new):
        """
        Check supplied data against historical data.
        If bad data, estimate replacement value.
        """
        data_history_RH = [info['RH'] for info in self.data_history]
        data_history_Tf = [info['Tf'] for info in self.data_history]

        data_history_RH = np.asarray(data_history_RH)
        data_history_Tf = np.asarray(data_history_Tf)
        
        
        # Done.
        return info_checked
        
        
class OutputWorkerThread(threading.Thread):
    def __init__(self, queue, thread_timeout=1.0, queue_timeout=0.1, *args, **kwargs):
        """
        Create new class instance.

        timeout is time after which this thread will self-destruct if its not being used.
        """
        threading.Thread.__init__(self, *args, **kwargs)
        self._queue = queue
        self._thread_timeout = thread_timeout
        self._queue_timeout = queue_timeout
        self._alive = False

        self._am_writing = False


    @property
    def is_empty(self):
        """
        Is output queue really empty?
        """
        flag_has_items = self._am_writing or self._queue.qsize() > 0

        flag_is_empty = not flag_has_items

        return flag_is_empty


    def run(self):
        """
        This is where the work happens.
        """

        # Main loop.
        self._alive = True
        time_reference = time.time()
        time_delta = 0

        while self._alive and time_delta < self._thread_timeout:
            time_delta = time.time() - time_reference

            try:
                # Block in queue until next item is available.
                info = self._queue.get(block=True, timeout=self._queue_timeout)

                self._am_writing = True

                # Write item to file.
                fname, item, args, kwargs = info
                try:
                    io.write(fname, item, *args, **kwargs)
                except IOError:
                    time_reference = time.time()
                    self._am_writing = False
                    raise

                # Reset timer.
                time_reference = time.time()
                self._am_writing = False

            except Queue.Empty:
                time.sleep(0.001)
                pass

            # Done.


    def stop(self):
        """
        Set flag to stop running.
        """
        self._alive = False







if __name__ == '__main__':
    pass
