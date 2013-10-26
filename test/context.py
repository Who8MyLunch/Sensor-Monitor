#!/usr/bin/python

from __future__ import division, print_function, unicode_literals


"""
Great idea from kennethreitz.org for allowing test module to import the package.
"""

import os
import sys

sys.path.insert(0, os.path.abspath('..'))

import nutmeg
