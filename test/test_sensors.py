
from __future__ import division, print_function, unicode_literals

import unittest

# import numpy as np

from context import sensor_monitor


class Test_Channel(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_does_it_import(self):
        self.assertTrue(hasattr(sensor_monitor, 'sensors'))
        self.assertTrue(hasattr(sensor_monitor.sensors, 'Channel'))

    def test_channel_init(self):
        pin_data = 25
        C = sensor_monitor.sensors.Channel_New(pin_data)
        self.assertTrue(C.pin == pin_data)

    def test_channel_start(self):
        pin_data = 25
        C = sensor_monitor.sensors.Channel_New(pin_data, time_wait=3.)
        gen = C.start()

        count = 0
        for t, RH, Tf in gen:
            self.assertTrue(C.keep_running)
            self.assertTrue(t > 1382845189.9)

            count += 1
            if count >= 2:
                C.stop()

        self.assertFalse(C.keep_running)


# Standalone.
if __name__ == '__main__':
    unittest.main(verbosity=2)
