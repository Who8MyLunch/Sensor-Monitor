
from __future__ import division, print_function, unicode_literals

import time
# import threading
import Queue
import random
import abc

# import numpy as np
# import pykalman
# import pykalman.sqrt

import dht22
# import utility
# import gen_multi


class Channel_Base(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, verbose=False):
        self._keep_running = False
        self._finished = False
        self.verbose = verbose

    def start(self):
        """Start the main event loop by calling subclass's run() method.
        """
        if self._finished:
            raise ValueError('Cannot restart a Channel after its been stopped.')

        if not self._keep_running:
            # Start the main loop.
            self._keep_running = True
            self.run()
        else:
            raise ValueError('Cannot start an already running Channel.')

        return self.run()

    def stop(self):
        """Shut down the sensor channel.
        """
        self._keep_running = False
        self._finished = True

    @abc.abstractmethod
    def run(self):
        """Start the generator main loop.  Yield data.
        """
        pass

    @property
    def is_running(self):
        return self._keep_running

    @property
    def is_finished(self):
        return self._finished

    def sleep(self, time_sleep):
        """Sleep for specified interval (seconds).  Check for instructions to terminate.
        """
        dt = 0.1
        time_zero = time.time()

        while (time.time() - time_zero < time_sleep) and self._keep_running:
            time.sleep(dt)

#################################################


class Channel_DHT22_Raw(Channel_Base):

    def __init__(self, pin, time_wait=5.0, **kwargs):
        """Read data from specified DHT22 sensor on specified GPIO pin.

        Parameters
        ----------
        pin : GPIO data pin

        time_wait : number of seconds between polling sensor for new data.

        """
        super(Channel_DHT22_Raw, self).__init__(**kwargs)

        self.pin = pin
        self.time_wait = time_wait

    def run(self):
        """Operate the generator main loop.  Yield sequence of tuples (time_read, RH, Tf).
        """
        time_last_good = time.time()
        self.keep_running = True

        while self.is_running:
            # Record some data.  Keyword delay specified in microseconds.
            RH, Tf = dht22.read_dht22_single(self.pin, delay=1)
            time_read = time.time()

            if RH:
                # Reading is good.
                time_last_good = time_read
                yield time_read, RH, Tf

            else:
                # Reading is not valid.
                if time.time() - time_last_good > 100.:
                    # Problem.  Stop looping.
                    self.stop()

            # Wait a bit before attempting another measurement.
            self.sleep(self.time_wait)

#################################################

class Channel_DHT22_Data_File(Channel_Base):

    def __init__(self, fname_data, time_wait=5.0, **kwargs):
        """Read raw DHT22 data from specified text file.

        Parameters
        ----------
        fname_data : File containing data samples.

        time_wait : number of seconds between polling sensor for new data.

        """
        super(Channel_DHT22_Data_File, self).__init__(**kwargs)

        self.fname = fname_data
        self.time_wait = time_wait

    def load_data(self, fname=None):
        """Load data samples from file.
        """
        if fname:
            self.fname = fname

        data = []
        with open(fname, 'r') as fi:
            for line in fi.readlines():


    def run(self):
        """Operate the generator main loop.  Yield sequence of tuples (time_read, RH, Tf).
        """
        time_last_good = time.time()
        self.keep_running = True

        while self.is_running:
            # Record some data.  Keyword delay specified in microseconds.
            RH, Tf = dht22.read_dht22_single(self.pin, delay=1)
            time_read = time.time()

            if RH:
                # Reading is good.
                time_last_good = time_read
                yield time_read, RH, Tf

            else:
                # Reading is not valid.
                if time.time() - time_last_good > 100.:
                    # Problem.  Stop looping.
                    self.stop()

            # Wait a bit before attempting another measurement.
            self.sleep(self.time_wait)


#################################################

class Channel_DHT22_Kalman(Channel_Base):

    def __init__(self, channel_raw, time_initialize=60, **kwargs):
        """Apply Kalman filter to raw data from raw channel.

        Parameters
        ----------
        channel_raw : Channel yielding raw data from a single DHT22 sensor.

        time_initialize : Number of seconds to spend collecting data for initialization.

        """
        super(Channel_DHT22_Kalman, self).__init__(**kwargs)

        if self.channel_raw.is_running:
            raise ValueError('Cannot instanciate using an already started channel.')

        self.channel_raw = channel_raw
        self.time_initialize = time_initialize

    def process_buffer(self, buffer_data):
        pass

    def filter(self, time_read, RH_raw, T_raw):
        dt = time_read - self.time_prior
        self.time_prior = time_read

    def run(self):
        """Operate main event loop.
        """
        buffer_data = []
        still_buffering = True
        time_zero = time.time()

        for time_read, RH_raw, T_raw in self.channel_raw.start():

            if still_buffering:
                # Collect initialization data.
                buffer_data.append((time_read, RH_raw, T_raw))
                RH_filter = RH_raw
                T_filter = T_raw

                if time.time() - time_zero > self.time_initialize:
                    self.process_buffer(buffer_data)
                    still_buffering = False
            else:
                RH_filter, T_filter = self.filter(time_read, RH_raw, T_raw)

            yield time_read, RH_filter, T_filter

#################################################

# _time_wait_default = 8.
# _time_history_default = 10*60
# class Channel(threading.Thread):
#     def __init__(self, pin, queue,
#                  time_wait=None, time_history=None, *args, **kwargs):
#         """
#         Record data from specified sensor pin.
#         time_wait: seconds between polling sensor
#         time_history: seconds of historical data remembered
#         """
#         threading.Thread.__init__(self, *args, **kwargs)
#         if not time_wait:
#             time_wait = _time_wait_default
#         if not time_history:
#             time_history = _time_history_default
#         self.num_min_history = 10  # minimum historical samples required to test for outliers.
#         self.check_threshold = 25  # error threshold for temperature and humidity.
#         self.pin = pin
#         self.time_wait = time_wait
#         self.time_history = time_history
#         self.data_history = []
#         self.data_latest = None
#         self.record_data = True
#         self.keep_running = False
#         self.queue = queue
#         # print('Channel start: %d' % self.pin)
#         # Done.
#     def run(self):
#         """
#         This is where the work happens.
#         """
#         self.keep_running = True
#         while self.keep_running:
#             time_zero = time.time()
#             if self.record_data:
#                 # Record some data.  delay in microseconds.
#                 RH, Tf = dht22.read_dht22_single(self.pin, delay=1)
#                 time_read = time.time()
#                 if not RH:
#                     # Reading is not valid.
#                     pass
#                 else:
#                     # Reading is good.  Store it.
#                     info = {'kind': 'sample',
#                             'pin': self.pin,
#                             'RH': float(np.round(RH, decimals=2)),
#                             'Tf': float(np.round(Tf, decimals=2)),
#                             'seconds': float(np.round(time_read, decimals=2))}
#                     self.add_data(info)
#             else:
#                 # Recording is paused.
#                 # print('recording paused: %d' % self.pin)
#                 pass
#             # Wait a bit before attempting another measurement.
#             dt = random.uniform(-0.1, 0.1)
#             time_delta = self.time_wait - (time_read - time_zero) + dt
#             if time_delta > 0:
#                 self.sleep(time_delta)
#         print('Channel exit: %d' % self.pin)
#     def sleep(self, time_sleep):
#         """
#         Sleep for specified interval.  Check for instructions to exit thread.
#         """
#         dt = 0.1
#         time_zero = time.time()
#         time_elapsed = 0.
#         while time_elapsed < time_sleep and self.keep_running:
#             time.sleep(dt)
#             time_elapsed = time.time() - time_zero
#     def stop(self):
#         """
#         Tell thread to stop running.
#         """
#         self.keep_running = False
#     def add_data(self, info):
#         """
#         Add new data point.
#         """
#         num_remain, num_removed = self.adjust_history()
#         if num_remain == 0 and num_removed > 0:
#             raise ValueError('No data remains in history.')
#         info = self.check_values(info)
#         self.data_history.append(info)
#         self.data_latest = info
#         try:
#             self.queue.put(info, block=False)
#         except Queue.Full as e:
#             print('TODO: implement better way to handle this exception: %s' % e)
#             raise e
#     def adjust_history(self):
#         """
#         Remove data from history if older than time window.
#         """
#         time_stamp_now = time.time()
#         # Look for data samples that are too old.
#         list_too_old = []
#         for d in self.data_history:
#             delta = time_stamp_now - d['seconds']
#             if delta > self.time_history:
#                 list_too_old.append(d)
#         # Remove old data from history.
#         for d in list_too_old:
#             self.data_history.remove(d)
#         # num_remain, num_removed
#         return len(self.data_history), len(list_too_old)
#     def _check_data_value(self, samples, value):
#         """
#         Check if sample is an outlier.  Replace with median.
#         """
#         value_med = np.median(samples)
#         delta = abs(value - value_med)
#         if delta > self.check_threshold:
#             # Fail.
#             value_checked = float(value_med)
#             msg = 'CHECK FAIL!  Replace: %.2f -> %.2f' % (value, value_checked)
#             print(msg)
#         else:
#             # Ok.
#             value_checked = value
#         return value_checked
#     def check_values(self, info_new):
#         """
#         Check supplied data against historical data.
#         If bad data, estimate replacement value.
#         """
#         if len(self.data_history) >= self.num_min_history:
#             data_history_RH = [info['RH'] for info in self.data_history]
#             data_history_Tf = [info['Tf'] for info in self.data_history]
#             RH_checked = self._check_data_value(data_history_RH, info_new['RH'])
#             Tf_checked = self._check_data_value(data_history_Tf, info_new['Tf'])
#             info_checked = info_new.copy()
#             info_checked['RH'] = RH_checked
#             info_checked['Tf'] = Tf_checked
#         else:
#             # Not enough history so just pass the the data through.
#             info_checked = info_new
#         return info_checked
#     @property
#     def freshness(self):
#         """
#         How fresh is the last recorded data?
#         """
#         if self.data_latest is None:
#             return None
#         else:
#             time_now = time.time()
#             delta_time = time_now - self.data_latest['seconds']
#             return delta_time
#     def pretty_sample_string(self, info):
#         """
#         Construct nice string representation of data sample information.
#         """
#         time_stamp_pretty = utility.pretty_timestamp(info['seconds'])
#         template = 'pin: %2d, Tf: %.1f, RH: %.1f, time: %s'
#         result = template % (self.pin, info['Tf'], info['RH'], time_stamp_pretty)
#         return result
    # def pretty_status(self):
    #     """
    #     Display current status.
    #     """
    #     print()
    #     print('Sensor Channel Status')
    #     print(' pin: %d' % self.pin)
    #     print(' length data_history: %d' % len(self.data_history))
    #     print(' length queue: %d' % self.queue.qsize())
    #     print(' queue full: %s' % self.queue.full())
    #     print(' queue empty: %s' % self.queue.empty())
    #     print(' is running: %s' % self.keep_running)
    #     print(' latest data: %s' % self.pretty_sample_string(self.data_latest))
    #     print(' freshness: %.1f seconds' % self.freshness)
    #     print()
#################################################
# def pause_channels(channels):
#     for c in channels:
#         c.record_data = False
# def unpause_channels(channels):
#     for c in channels:
#         c.record_data = True


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

if __name__ == '__main__':
    pass
