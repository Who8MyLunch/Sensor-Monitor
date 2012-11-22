
from __future__ import division, print_function, unicode_literals

import os
import argparse

import upload
import sensors


def run_upload():
    """
    Do the work to upload to my Fusion Table.
    """

    
def run_record()
    """
    Do the work to record data from sensors.
    """
    
  
    
    

def main():
    """
    This is the main application.
    """

    # Build the parser.
    parser = argparse.ArgumentParser()
    parser.add_argument('-U', '--upload', default=False, action='store_true', help='Upload sensor data to my Fusion Table.')
    parser.add_argument('-R', '--record', default=False, action='store_true', help='Record data from DHT22 sensors.')

    # Parse command line input, do the work.
    args = parser.parse_args()
    
    if args.upload:
        run_upload():
    elif args.record:
        run_record()
    else:
        print()
        print('Error!  Must supply command-line argument.')
        
    # Done.


if __name__ == '__main__':
    main()

    
    
