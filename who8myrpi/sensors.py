
from __future__ import division, print_function, unicode_literals

import os
import time
import threading
import Queue
import random

import numpy as np

import dht22
import utility

#################################################
# Helper functions.


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


#################################################
# Data record.


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
            RH = float((np.left_shift(byte_1, 8) + byte_2) / 10.)
            Tc = float((np.left_shift(byte_3, 8) + byte_4) / 10.)
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


#################################################


_time_wait_default = 8.
_time_history_default = 10*60


class Channel(threading.Thread):
    def __init__(self, pin, queue,
                 time_wait=None, time_history=None, *args, **kwargs):
        """
        Record data from specified sensor pin.

        time_wait: seconds between polling sensor
        time_history: seconds of historical data remembered
        """

        threading.Thread.__init__(self, *args, **kwargs)

        if not time_wait:
            time_wait = _time_wait_default

        if not time_history:
            time_history = _time_history_default

        self.num_min_history = 10  # minimum historical samples required to test for outliers.
        self.check_threshold = 25  # error threshold for temperature and humidity.
        self.pin = pin
        self.time_wait = time_wait
        self.time_history = time_history
        self.data_history = []
        self.data_latest = None

        self.record_data = True
        self.keep_running = False
        self.queue = queue

        # print('Channel start: %d' % self.pin)

        # Done.

    def run(self):
        """
        This is where the work happens.
        """
        self.keep_running = True
        while self.keep_running:
            time_zero = time.time()

            if self.record_data:
                # Record some data.  delay in microseconds.
                RH, Tc = read_dht22_single(self.pin, delay=1)
                time_read = time.time()

                if not RH:
                    # Reading is not valid.
                    pass
                else:
                    # Reading is good.  Store it.
                    info = {'kind': 'sample',
                            'pin': self.pin,
                            'RH': float(np.round(RH, decimals=2)),
                            'Tf': float(np.round(c2f(Tc), decimals=2)),
                            'seconds': float(np.round(time_read, decimals=2))}

                    self.add_data(info)
            else:
                # Recording is paused.
                # print('recording paused: %d' % self.pin)
                pass

            # Wait a bit before attempting another measurement.
            dt = random.uniform(-0.1, 0.1)
            time_delta = self.time_wait - (time_read - time_zero) + dt
            if time_delta > 0:
                self.sleep(time_delta)

        print('Channel exit: %d' % self.pin)

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
            self.queue.put(info, block=False)
        except Queue.Full as e:
            print('TODO: implement better way to handle this exception: %s' % e)
            raise e

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

        # num_remain, num_removed
        return len(self.data_history), len(list_too_old)

    def _check_data_value(self, samples, value):
        """
        Check if sample is an outlier.  Replace with median.
        """
        value_med = np.median(samples)
        delta = abs(value - value_med)

        if delta > self.check_threshold:
            # Fail.
            value_checked = float(value_med)
            msg = 'CHECK FAIL!  Replace: %.2f -> %.2f' % (value, value_checked)
            print(msg)

        else:
            # Ok.
            value_checked = value

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
        template = 'pin: %2d, Tf: %.1f, RH: %.1f, time: %s'
        result = template % (self.pin, info['Tf'], info['RH'], time_stamp_pretty)

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

#################################################


def stop_channels(channels):
    """
    Callstop method on all channels.
    Block until all channels exit.
    """
    if channels:
        for c in channels:
            if c:
                c.stop()
        for c in channels:
            if c:
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
        c = Channel(p, queue=queue)
        c.start()
        channels.append(c)

        # Random small pause before creating next channel.
        dt = random.uniform(0.0, 0.1)
        time.sleep(dt)

    # Done.
    return channels, queue


def check_channels_ok(channels, time_wait_max=None, verbose=False):
    """
    Ensure all channels are recording ok.
    time_wait_max: maximum number of seconds to wait for all sensors to be ready.
    """
    if not time_wait_max:
        time_wait_max = 90  # seconds

    count_ready = 0
    time_elapsed = 0
    time_zero = time.time()

    num_channels = len(channels)

    # Main loop.
    while not (time_elapsed > time_wait_max or count_ready == num_channels):
        # Keep looping until all channels pass, or until timeout.
        time.sleep(.2)

        # Count number of channels with collected data.
        count_ready_test = 0
        pins_ready = []
        for c in channels:
            if c.data_latest:
                pins_ready.append(c.pin)
                count_ready_test += 1

        if count_ready_test > count_ready:
            count_ready = count_ready_test
            if verbose:
                print('Channels ok: %d of %d  %s' % (count_ready, num_channels, pins_ready))

        time_elapsed = time.time() - time_zero

    # Finish.
    if count_ready == num_channels:
        return True
    else:
        return False

#######################################################


def data_collector(queue, time_interval=60):
    """
    This is a generator.

    Record data for an experiment from multiple sensors.
    Keep recording for specified time interval (seconds).
    Return all accumulated data at end of interval.
    """

    # Main loop.
    while True:
        try:
            # Wait a bit for some data to accumulate in the queue.
            time.sleep(time_interval)

            samples = []
            while not queue.empty():
                info = queue.get()
                samples.append(info)

            if samples:
                # Yield data to the caller.
                yield samples

        except GeneratorExit:
            print('\nData collector: GeneratorExit')
            break

        except KeyboardInterrupt:
            print('\nData collector: User stop!')
            break

#################################################


def example_single():
    """
    Read multiple data samples from single sensor over short period of time.
    """

    pin = 25

    num_samples = 10
    time_wait = 5.  # seconds

    print('\npin: %d\n' % pin)

    for k in range(num_samples):
        RH, Tc = read_dht22_single(pin)

        if RH:
            print('RH: %.1f, Tc: %.1f' % (RH, Tc))
        else:
            print('Error: %s' % Tc)

        time.sleep(time_wait)

#################################################

if __name__ == '__main__':
    # Examples.
    example_single()
