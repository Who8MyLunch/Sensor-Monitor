
from __future__ import division, print_function, unicode_literals

import os
import time
import threading
import Queue
import random

import numpy as np

import dht22
import utility

##################################################
# Helper functions.
#
def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p


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



##################################################



# def check_pin_connected(pin_data):
    # """
    # Run some tests to see if data pin appears to be connected to sensor.
    # """
    # first, bits = dht22.read_bits(pin_data)
    # if first is None:
        # return False
    # else:
        # return True
    # # Done.



##################################################
# Data record.
#
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
        # Total number of bits is Ok.
        byte_1, byte_2, byte_3, byte_4, ok = bits_to_bytes(bits)

        if ok:
            # Checksum is OK.
            RH = float( (np.left_shift(byte_1, 8) + byte_2) / 10. )
            Tc = float( (np.left_shift(byte_3, 8) + byte_4) / 10. )
        else:
            # Problem!
            msg = 'Fail checksum'
            RH, Tc = None, msg

    else:
        # Problem.
        msg = 'Fail len(bits) != 40 [%d]' % (len(bits))
        RH, Tc = None, msg

    # Done.
    return RH, Tc


##################################################

_time_wait_default = 10.
_time_history_default = 10*60

class Channel(threading.Thread):
    def __init__(self, pin, queue=None,
                 pin_err=None, pin_ok=None,
                 time_wait=None, time_history=None, *args, **kwargs):
        """
        Record data from specified sensor pin.

        time_wait: seconds between polling sensor
        time_history: seconds of historical data remembered
        """

        threading.Thread.__init__(self, *args, **kwargs)

        if time_wait is None:
            time_wait = _time_wait_default

        if time_history is None:
            time_history = _time_history_default

        if queue is None:
            queue = Queue.Queue()

        self.pin_err = pin_err
        self.pin_ok = pin_ok

        self.num_min_history = 10
        self.check_threshold = 25
        self.pin = pin
        self.time_wait = time_wait
        self.time_history = time_history
        self.data_history = []
        self.data_latest = None

        self.record_data = True
        self.keep_running = False
        self.queue = queue

        # Done.


    def run(self):
        """
        This is where the work happens.
        """
        self.keep_running = True
        while self.keep_running:
            time_zero = time.time()

            if self.record_data:
                # Record some data.
                RH, Tc = read_dht22_single(self.pin, delay=1)

                if RH is None:
                    # Reading is not valid.
                    pass
                else:
                    # Reading is good.  Store it.
                    info = {'kind': 'sample',
                            'pin': self.pin,
                            'RH': float(np.round(RH, decimals=2)),
                            'Tf': float(np.round(c2f(Tc), decimals=2)),
                            'seconds': float(np.round(time.time(), decimals=2))}

                    info = self.add_data(info)
                    #print(self.pretty_sample_string(info))
            else:
                # Recording is paused.
                # print('recording paused: %d' % self.pin)
                pass

            # Wait a bit before attempting another measurement.
            dt = random.uniform(-0.05, 0.05)
            time_delta = self.time_wait - (time.time() - time_zero) + dt
            if time_delta > 0:
                self.sleep(time_delta)

            # Repeat loop.

        print('Channel exit: %d.' % self.pin)
        self.status_indicator(-1)

        # Done.


    def status_indicator(self, ok):
        """
        Configure and set status LEDs.

        ok  > 0: 'ok'
        ok == 0: 'error'
        ok  < 0: 'off'
        """
        if not (self.pin_ok == None or self.pin_err == None):
            # Status pins are defined.
            # These pins assumed already be configured for output.
            if ok > 0:
                # Everything is OK.
                dht22._digitalWrite(self.pin_ok, dht22._HIGH)
                dht22._digitalWrite(self.pin_err, dht22._LOW)
            elif ok == 0:
                # Not ok.  Problem.
                dht22._digitalWrite(self.pin_err, dht22._HIGH)
                dht22._digitalWrite(self.pin_ok, dht22._LOW)
            else:
                # Off.
                dht22._digitalWrite(self.pin_err, dht22._LOW)
                dht22._digitalWrite(self.pin_ok, dht22._LOW)

        else:
            # No status pins configured.  Do nothing.
            pass

    # Done.



    def sleep(self, time_sleep):
        """
        Sleep for specified interval.  Check for instructions to exit thread.
        """
        dt = 0.1

        time_zero = time.time()
        time_elapsed = 0.

        while time_elapsed < time_sleep and self.keep_running:
            time.sleep(dt)
            time_elapsed = time.time() - time_zero

        # Done.


    def stop(self):
        """
        Tell thread to stop running.
        """
        self.keep_running = False


    def add_data(self, info):
        """
        Add new data point.
        """
        num_remain, num_removed = self.adjust_history()

        if num_remain == 0 and num_removed > 0:
            raise ValueError('No data remains in history.')

        info = self.check_values(info)

        self.data_history.append(info)
        self.data_latest = info

        try:
            block = False
            self.queue.put(info, block)
        except Queue.Full as e:
            print('TODO: implement better way to handle this exception: %s' % e)
            raise e

        # Done.
        return info


    def adjust_history(self):
        """
        Remove data from history if older than time window.
        """
        time_stamp_now = time.time()

        # Look for data samples that are too old.
        list_too_old = []
        for d in self.data_history:
            delta = time_stamp_now - d['seconds']

            if delta > self.time_history:
                list_too_old.append(d)

        # Remove old data from history.
        for d in list_too_old:
            self.data_history.remove(d)

        # Done.
        num_remain, num_removed = len(self.data_history), len(list_too_old)
        return num_remain, num_removed


    def _check_data_value(self, samples, value):
        value_med = np.median(samples)
        delta = abs(value - value_med)

        if delta > self.check_threshold:
            # Fail.
            print('CHECK FAIL!  Replace with historical median value.')

            value_checked = float(value_med)

        else:
            # Ok.
            value_checked = value

        # Done.
        return value_checked


    def check_values(self, info_new):
        """
        Check supplied data against historical data.
        If bad data, estimate replacement value.
        """
        if len(self.data_history) >= self.num_min_history:
            data_history_RH = [info['RH'] for info in self.data_history]
            data_history_Tf = [info['Tf'] for info in self.data_history]

            RH_checked = self._check_data_value(data_history_RH, info_new['RH'])
            Tf_checked = self._check_data_value(data_history_Tf, info_new['Tf'])

            info_checked = info_new.copy()
            info_checked['RH'] = RH_checked
            info_checked['Tf'] = Tf_checked
        else:
            # Not enough history so just pass the the data through.
            info_checked = info_new

        # Done.
        return info_checked


    @property
    def freshness(self):
        """
        How fresh is the last recorded data?
        """
        if self.data_latest is None:
            return None
        else:
            time_now = time.time()
            delta_time = time_now - self.data_latest['seconds']

            return delta_time


    def pretty_sample_string(self, info):
        """
        Construct nice string representation of data sample information.
        """
        time_stamp_pretty = utility.pretty_timestamp(info['seconds'])
        result = 'pin: %2d, Tf: %.1f, RH: %.1f, time: %s' % (self.pin, info['Tf'], info['RH'], time_stamp_pretty)

        return result


    def pretty_status(self):
        """
        Display current status.
        """
        print()
        print('Sensor Channel Status')
        print(' pin: %d' % self.pin)
        print(' length data_history: %d' % len(self.data_history))
        print(' length queue: %d' % self.queue.qsize())
        print(' queue full: %s' % self.queue.full())
        print(' queue empty: %s' % self.queue.empty())
        print(' is running: %s' % self.keep_running)
        print(' latest data: %s' % self.pretty_sample_string(self.data_latest))
        print(' freshness: %.1f seconds' % self.freshness)
        print()



##################################################

def stop_channels(channels):
    """
    Callstop method on all channels.
    Block until all channels exit.
    """
    for c in channels:
        c.stop()
    for c in channels:
        c.join()

    # Done.


def pause_channels(channels):
    for c in channels:
        c.record_data = False

def unpause_channels(channels):
    for c in channels:
        c.record_data = True


def start_channels(pins_data):
    """
    Turn on all recording channels.
    Verify all are recording valid data.
    """

    # Build queue for collecting all data samples.
    queue = Queue.Queue(maxsize=1000)

    # Build and start the channel recorders.
    channels = []
    for p in pins_data:
        c = Channel(p, queue=queue) #, time_wait=time_wait, time_history=time_history)
        c.start()
        channels.append(c)

        # Random small pause before creating next channel.
        dt = random.uniform(0.0, 0.1)
        time.sleep(dt)

    # Done.
    return channels, queue



def check_channels_ok(channels, verbose=False):
    """
    Ensure all channels are recording ok.
    """
    all_channels_ok = False
    time_wait_max = 60  # seconds
    time_elapsed = 0.
    time_zero = time.time()

    while not (time_elapsed > time_wait_max or all_channels_ok):
        # Keep looping until all channels pass, or until timeout.
        time.sleep(1)
        count_ready = 0
        for c in channels:
            if c.data_latest is not None:
                count_ready += 1

        if count_ready == len(channels):
            # Everything is good to go.
            all_channels_ok = True

        time_elapsed = time.time() - time_zero
        if verbose:
            print('channels ok: %d of %d' % (count_ready, len(channels)))

    # Finish.
    if not all_channels_ok:
        stop_all_channels(channels)
        # raise ValueError('Only %d channels ready (out of %d) after waiting %s seconds.' %
                         # (count_ready, len(channels), time_wait_max))

    # Done.
    return all_channels_ok


#######################################################

def data_collector(queue, time_interval=30):
    """
    Record data for an experiment from multiple sensors.
    Keep recording for specified time interval (seconds).
    Return all accumulated data at end of interval.
    """

    # Main loop.
    keep_looping = True
    while keep_looping:
        try:
            # Wait a bit for some data to accumulate in the queue.
            time.sleep(time_interval)

            samples = []
            while not queue.empty():
                info = queue.get()
                samples.append(info)

            if len(samples) > 0:
                # Pretty status message.
                t = data_collected[0]['seconds']
                fmt = '%Y-%m-%d %H-%M-%S'
                time_stamp = utility.pretty_timestamp(t, fmt)
                print('write:%3d [%s]' % (len(samples), time_stamp) )

                # Send data to the caller.
                yield samples

        except GeneratorExit:
            print()
            print('Data collector: GeneratorExit')
            keep_looping = False
            
        except KeyboardInterrupt:
            print()
            print('Data collector: User stop!')
            keep_looping = False
        
    # Done.




# _header = ['pin', 'RH_avg', 'RH_std', 'Tf_avg', 'Tf_std', 'Samples', 'Time']
# def write_data_samples(sensor_name, info_results, path_data=None):
    # """
    # Save experiment data record to file.
    # """
    # if path_data is None:
        # path_base = os.path.curdir
        # folder_data = 'data'
        # path_data = os.path.join(path_base, folder_data)
    # if not os.path.isdir(path_data):
        # os.mkdir(path_data)
    # t = info_results[0]['Time']
    # d = datetime.datetime.utcfromtimestamp(t)
    # time_stamp = d.strftime('%Y-%m-%d - %H-%M-%S')
    # folder_day = d.strftime('%Y-%m-%d')
    # path_day = os.path.join(path_data, folder_day)
    # if not os.path.isdir(path_day):
        # os.mkdir(path_day)
    # # Output to file.
    # fname = sensor_name + ' - ' + time_stamp + '.csv'
    # f = os.path.join(path_day, fname)
    # data = []
    # for info_sample in info_results:
        # line = [info_sample[k] for k in _header]
        # data.append(line)
    # io.write(f, data, header=_header)
    # # Done.
# def read_dht22(pins_data, recording_interval=60, delta_time_wait=2.1,
               # pin_ok=None, pin_err=None, pin_power=None):
    # """
    # Read data from dht22 sensor.  Collect data over short time interval.  Return median value.
    # Ignore any invalid data values.
    # pins_data = integer or sequence of integers.
    # recording_interval = recording time interval in seconds.
    # delta_time_wait = time delay between attempts to read from sensors.  Must be at least 2 seconds.
    # """
    # if np.isscalar(pins_data):
        # pins_data = [pins_data]
    # if delta_time_wait < 2:
        # raise ValueError('Invalid value for delta_time_wait: %s' % delta_time_wait)
    # # Setup data containers.
    # num_pin = len(pins_data)
    # info_data = [None] * num_pin
    # for k in range(num_pin):
        # info_data[k] = {'pin': None,
                        # 'RH': [],
                        # 'Tc': [],
                        # 'time': []}
    # # Main loop over data sampling time interval.
    # time_start = time.time()
    # time_run = 0.
    # while time_run < recording_interval:
        # set_status_led(-1, pin_ok, pin_err)
        # time.sleep(delta_time_wait)
        # # Loop over sensor pins.
        # for k, pin in enumerate(pins_data):
            # value = read_dht22_single(pin)
            # time_now = time.time()
            # time_run = time_now - time_start
            # if value[0] is None:
                # # Problem with sensor measurement.
                # set_status_led(0, pin_ok, pin_err)
                # message = value[1]
                # RH, Tc = -1, -1
                # # print('problem with pin: %d' % pin)
                # # print(message)
            # else:
                # # Measurement OK.
                # set_status_led(1, pin_ok, pin_err)
                # RH, Tc = value
                # # print('ok', RH, Tc)
            # info_data[k]['pin'] = pin
            # info_data[k]['RH'].append(RH)
            # info_data[k]['Tc'].append(Tc)
            # info_data[k]['time'].append(time_now)
    # # print(info_data)
    # set_status_led(-1, pin_ok, pin_err)
    # # Finish.
    # eps = 1.e-5
    # info_results = []
    # for info_data_k in info_data:
        # pin = info_data_k['pin']
        # data_RH = np.asarray(info_data_k['RH'])
        # data_Tc = np.asarray(info_data_k['Tc'])
        # data_time = np.asarray(info_data_k['time'])
        # data_Tf = c2f(data_Tc)
        # whr_valid = np.where(data_RH > 0)
        # num_valid = len(whr_valid[0])
        # if num_valid > 0:
            # RH_avg = np.mean(data_RH[whr_valid])
            # RH_std = np.std(data_RH[whr_valid])
            # Tf_avg = np.mean(data_Tf[whr_valid])
            # Tf_std = np.std(data_Tf[whr_valid])
            # Samples = len(data_RH[whr_valid])
            # Time = np.mean(data_time[whr_valid])
            # RH_avg = np.round(RH_avg, 3)
            # RH_std = np.round(RH_std, 3)
            # Tf_avg = np.round(Tf_avg, 3)
            # Tf_std = np.round(Tf_std, 3)
            # Time = np.round(Time, 2)
            # info_sample = {'pin':    pin,
                           # 'RH_avg': RH_avg,
                           # 'RH_std': RH_std,
                           # 'Tf_avg': Tf_avg,
                           # 'Tf_std': Tf_std,
                           # 'Samples': Samples,
                           # 'Time':   Time}
            # if info_sample['RH_std'] < eps:
                # info_sample['RH_std'] = 0.0
            # if info_sample['Tf_std'] < eps:
                # info_sample['Tf_std'] = 0.0
            # info_results.append(info_sample)
        # else:
            # # Problem??
            # print('No valid samples for pin %d' % pin)
    # # Average time stamp over all data observations.
    # vals = [info_sample['Time'] for info_sample in info_results]
    # time_avg = np.round(np.mean(vals), 3)
    # for info_sample in info_results:
        # info_sample['Time'] = time_avg
    # # Done.
    # return info_results
# def build_summary(info_results, info_summary=None, pins_data=None):
    # """
    # Summary of collected data.
    # """
    # if info_summary is None:
        # info_summary = {}
        # if pins_data is not None:
            # for p in pins_data:
                # info_summary[p] = 0
    # for info_sample in info_results:
        # p = info_sample['pin']
        # n = info_sample['Samples']
        # if not p in info_summary:
            # info_summary[p] = 0
        # info_summary[p] += n
    # # Done.
    # return info_summary
# def pretty_status(time_now, info_summary):
    # """
    # Display pretty status update.
    # """
    # d = datetime.datetime.utcfromtimestamp(time_now)
    # time_stamp = d.strftime('%Y-%m-%d %H:%M:%S')
    # pin_count_str = ''
    # for p, n in info_summary.items():
        # s = '%3d' % (n)
        # pin_count_str += s + ' '
    # msg = '%s || %s' % (time_stamp, pin_count_str)
    # print(msg)
    # # Done.
# def example_single():
    # pin_power = 22
    # pin_data = 25
    # dht22.SetupGpio()
    # dht22._pinMode(pin_power, dht22._OUTPUT)
    # dht22._digitalWrite(pin_power, dht22._HIGH)
    # c = Channel(pin_data)
    # c.start()
# def example_multiple():
    # pin_power = 22
    # pins_data = [4, 17, 18, 21, 23]
    # path_data = os.path.join(os.path.abspath(os.path.curdir), 'data')
    # collect_data(pins_data, path_data,
                 # pin_ok=None, pin_err=None, pin_power=pin_power)


if __name__ == '__main__':
    # Examples.
    example_multiple()

