
from distribute_setup import use_setuptools
use_setuptools()

import numpy as np
import setuptools

from setuptools import setup, find_packages
from setuptools.extension import Extension

from Cython.Distutils import build_ext



# WiriingPi source, includes, and options.
include_dirs = ['who8myrpi',
                'who8myrpi/wiringPi',
                setuptools.distutils.sysconfig.get_python_inc(),
                np.get_include()]

extra_compile_args = []
extra_link_args = []

source_wiringPi = ['who8myrpi/wiringPi/wiringPi.c',
                   'who8myrpi/wiringPi/wiringPiSPI.c',
                   'who8myrpi/wiringPi/wiringSerial.c',
                   'who8myrpi/wiringPi/wiringShift.c',
                   'who8myrpi/wiringPi/softPwm.c',
                   'who8myrpi/wiringPi/piThread.c',
                   'who8myrpi/wiringPi/gertboard.c',
                   'who8myrpi/wiringPi/wiringPiFace.c',
                   'who8myrpi/wiringPi/lcd.c',
                   'who8myrpi/wiringPi/piHiPri.c']

# GPIO extension.
source_files = ['who8myrpi/_gpio.pyx'] + source_wiringPi

ext_gpio = Extension('_gpio', source_files,
                     language='c++',
                     include_dirs=include_dirs,
                     extra_compile_args=extra_compile_args,
                     extra_link_args=extra_link_args)

# Timing example.
source_files = ['who8myrpi/measure_timing.pyx']  + source_wiringPi

ext_timing = Extension('measure_timing', source_files,
                       language='c++',
                       include_dirs=include_dirs,
                       extra_compile_args=extra_compile_args,
                       extra_link_args=extra_link_args)

# DHT22 sensor interface.
source_files = ['who8myrpi/dht22.pyx']  + source_wiringPi

ext_dht22 = Extension('dht22', source_files,
                      language='c++',
                      include_dirs=include_dirs,
                      extra_compile_args=extra_compile_args,
                      extra_link_args=extra_link_args)

###############################

# Do it.
version = '2012.09.29'

setup(name='Who8MyRPi',
      packages=find_packages(),
      package_data={'': ['*.txt', '*.md', '*.cpp', '*.pyx', '*.pxd']},
      cmdclass={'build_ext':build_ext},
      ext_modules=[ext_gpio, ext_dht22, ext_timing],

      # Metadata
      version=version,
      author='Pierre V. Villeneuve',
      author_email='pierre.villeneuve@gmail.com',
      description='My Fun Stuff with the RaspberryPi')
