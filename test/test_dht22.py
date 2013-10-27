
from __future__ import division, print_function, unicode_literals

# import os
import time
import unittest

# import numpy as np

from context import sensor_monitor


class Test_Basic_Read_Some_Data(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_does_it_import(self):
        self.assertTrue(hasattr(sensor_monitor, 'dht22'))
        self.assertTrue(hasattr(sensor_monitor.dht22, 'read_bits'))
        self.assertTrue(hasattr(sensor_monitor.dht22, 'read_dht22_single'))

    def test_read_a_valid_value(self):
        pin_data = 25
        pin_power = 22

        if pin_power:
            sensor_monitor.dht22._pinMode(pin_power, sensor_monitor.dht22._OUTPUT)
            sensor_monitor.dht22._digitalWrite(pin_power, True)
            time.sleep(5)

        # seconds.
        time_max = 60.
        time_wait = 5.

        time_0 = time.time()
        flag = False
        while time.time() - time_0 < time_max:
            RH, Tc = sensor_monitor.dht22.read_dht22_single(pin_data)

            if RH:
                flag = True
                print('RH: %.1f, Tc: %.1f' % (RH, Tc))
                break
            else:
                print('Error: %s' % Tc)

            time.sleep(time_wait)

        self.assertTrue(flag)

# Standalone.
if __name__ == '__main__':
    unittest.main(verbosity=2)
