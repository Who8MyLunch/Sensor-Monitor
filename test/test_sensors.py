
from __future__ import division, print_function, unicode_literals

import os
import unittest
from context import sensor_monitor

path_module = os.path.normpath(os.path.dirname(__file__))


class Test_Channel(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_does_it_import(self):
        self.assertTrue(hasattr(sensor_monitor, 'sensors'))
        self.assertTrue(hasattr(sensor_monitor.sensors, 'Channel_Base'))
        self.assertTrue(hasattr(sensor_monitor.sensors, 'Channel_DHT22_Raw'))
        self.assertTrue(hasattr(sensor_monitor.sensors, 'Channel_DHT22_Kalman'))
        self.assertTrue(hasattr(sensor_monitor.sensors.Channel_Base, 'start'))
        self.assertTrue(hasattr(sensor_monitor.sensors.Channel_DHT22_Raw, 'run'))
        self.assertTrue(hasattr(sensor_monitor.sensors.Channel_DHT22_Kalman, 'run'))

    def test_channel_raw_init(self):
        pin_data = 25
        C = sensor_monitor.sensors.Channel_DHT22_Raw(pin_data)
        self.assertTrue(C.pin == pin_data)

    def test_channel_raw_start(self):
        pin_data = 25
        C = sensor_monitor.sensors.Channel_DHT22_Raw(pin_data, time_wait=3.)

        count = 0
        for t, RH, Tf in C.start():
            self.assertFalse(C.is_finished)
            self.assertTrue(C.is_running)
            self.assertTrue(t > 1382845189.9)

            count += 1
            if count >= 1:
                C.stop()

        self.assertTrue(C.is_finished)
        self.assertFalse(C.is_running)

    def test_channel_file_init(self):
        fname = os.path.join(path_module, '..', 'sensor_monitor', 'sample_data_10_min.txt')
        C = sensor_monitor.sensors.Channel_DHT22_Data_File(fname)
        print(C.data.shape)
        # self.assertTrue(C.data == pin_data)

    def test_channel_file_start(self):
        fname = os.path.join(path_module, '..', 'sensor_monitor', 'sample_data_10_min.txt')
        C = sensor_monitor.sensors.Channel_DHT22_Data_File(fname)

        count = 0
        for t, RH, Tf in C.start():
            self.assertFalse(C.is_finished)
            self.assertTrue(C.is_running)
            self.assertTrue(t > 1382845189.9)

            count += 1
            if count >= 1:
                C.stop()

        self.assertTrue(C.is_finished)
        self.assertFalse(C.is_running)


# Standalone.
if __name__ == '__main__':
    unittest.main(verbosity=2)
