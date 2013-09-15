
from __future__ import division, print_function, unicode_literals

import os
import time
import threading

import RPIO

class Blinker(threading.Thread):
    def __init__(self, pin, freq=1, auto_start=True, *args, **kwargs):
        """
        Make an LED blink.
        pin: GPIO pin number.
        freq: Blinking frequency (Hz)

        Set freqency to zero to temporarily disable LED.
        """

        threading.Thread.__init__(self, *args, **kwargs)

        self.lock = threading.Lock()
        self.pin = pin
        self.time_interval = 0
        self.time_pause = 0.01
        self.frequency = freq
        self.timeout = 0

        RPIO.setwarnings(False)
        RPIO.setup(self.pin, RPIO.OUT, initial=False)

        if auto_start:
            self.start()

        # Done.



    def run(self):
        """
        This is where the work happens.
        """
        time_base = time.time()
        self.keep_running = True

        while self.keep_running:
            time.sleep(self.time_pause)

            time_now = time.time()

            if self.time_interval <= 0:
                # Off.
                RPIO.output(self.pin, False)

            elif time_now - time_base > self.time_interval:
                time_base = time_now

                # Reverse LED state.
                value = RPIO.input(self.pin)
                RPIO.output(self.pin, not value)

            # Repeat loop.

        print('Blinker exit: %d' % self.pin)
        RPIO.output(self.pin, False)

        # Done.



    def stop(self):
        """
        Tell thread to stop running.
        """
        self.lock.acquire()
        self.keep_running = False
        self.lock.release()



    @property
    def frequency(self):
        """
        Blinking frequency, Hz.
        """
        self.lock.acquire()
        try:
            val = 1./self.time_interval
        except ZeroDivisionError:
            val = 0

        self.lock.release()

        return val



    @frequency.setter
    def frequency(self, freq):

        self.lock.acquire()

        if freq > 0:
            self.time_interval = 1./freq
        else:
            self.time_interval = 0

        self.lock.release()
