
from __future__ import division, print_function, unicode_literals

import os
import time
import unittest

import numpy as np

from context import sensor_monitor


def gen_alpha(N, time_wait):
    for k in range(N):
        val = np.random.random_integers(65, 65+25)
        val = chr(val)
        time.sleep(time_wait)
        yield val

def gen_numeric(N, time_wait):
    for k in range(N):
        val = np.random.random_integers(35, 35+25)
        val = str(val)
        time.sleep(time_wait)
        yield val


class Test_Multiplex(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_does_it_import(self):
        self.assertTrue(hasattr(sensor_monitor, 'multiplex'))
        self.assertTrue(hasattr(sensor_monitor.multiplex, 'generate'))

    def test_scenario_A(self):
        time_slow = 0.1
        time_fast = 0.01
        num_samples = 10

        sources = (gen_alpha(num_samples, time_slow),
                   gen_numeric(num_samples, time_fast))
                   # gen_numeric(num_samples, time_fast))
        gen_combo = sensor_monitor.multiplex.generate(sources)

        c_alpha = 0
        c_numeric = 0
        for value in gen_combo:
            c_alpha += value.isalpha()
            c_numeric += value.isdigit()
            # print(value)

        self.assertTrue(c_alpha == num_samples)
        self.assertTrue(c_numeric == num_samples)

    def test_scenario_B(self):
        time_slow = 0.1
        time_fast = 0.01
        num_samples = 10

        sources = (gen_alpha(num_samples, time_slow),
                   gen_numeric(num_samples, time_slow),
                   gen_numeric(num_samples, time_fast))
        gen_combo = sensor_monitor.multiplex.generate(sources)

        c_alpha = 0
        c_numeric = 0
        v_test = None
        for value in gen_combo:
            c_alpha += value.isalpha()
            c_numeric += value.isdigit()
            # print(value, c_alpha, c_numeric)

            if not v_test and value.isalpha():
                v_test = c_numeric

        self.assertTrue(c_alpha == num_samples)
        self.assertTrue(c_numeric == 2*num_samples)
        self.assertTrue(v_test == 8)

# Standalone.
if __name__ == '__main__':
    unittest.main(verbosity=2)

