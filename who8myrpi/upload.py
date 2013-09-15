
from __future__ import division, print_function, unicode_literals

import os
import shutil
import glob
import datetime
import time

import numpy as np
import data_io as io

import who8mygoogle.fusion_tables as fusion_tables
import utility
import blinker

from coroutine import coroutine

# Static stuff.
column_types = [['DateTime',    fusion_tables.fusion_table.TYPE_DATETIME],
                ['Seconds',     fusion_tables.fusion_table.TYPE_NUMBER],
                ['Kind',        fusion_tables.fusion_table.TYPE_STRING],
                ['Pin',         fusion_tables.fusion_table.TYPE_NUMBER],
                ['Temperature', fusion_tables.fusion_table.TYPE_NUMBER],
                ['Humidity',    fusion_tables.fusion_table.TYPE_NUMBER]]

fname_client = 'client_secrets.json'
api_name = 'fusiontables'

#################################################


def connect_table(table_name, path_credentials):
    """
    Establish credentials and retrieve API service object.
    """

    f = os.path.join(path_credentials, fname_client)
    credentials = fusion_tables.authorize.build_credentials(f, api_name)
    service = fusion_tables.authorize.build_service(api_name, credentials)

    tableId = fusion_tables.fusion_table.fetch_table(service, table_name, column_types)

    # Done.
    return service, tableId



def process_samples(samples):
    """
    Convert sensor-generated samples to data rows appropriate to upload to Fusion Table.
    """
    fields_to_columns = ['seconds',
                         'kind',
                         'pin',
                         'Tf',
                         'RH']

    # Loop over all samples.  Convert each to a Fusion Table row.
    data_rows = []
    for info in samples:
        row = [info[n] for n in fields_to_columns]

        seconds = row[0]
        time_stamp = utility.pretty_timestamp(seconds)
        row.insert(0, time_stamp)

        data_rows.append(row)

    # Finish.
    column_names = fields_to_columns
    column_names.insert(0, 'DateTime')

    # Done.
    return data_rows, column_names



@coroutine
def data_uploader(service, tableId, pin_status):
    """
    Coroutine to receive new data and upload to a Google Fusion table.
    """
    if pin_status:
        blink_status = blinker.Blinker(pin_status)

    keep_looping = True
    while keep_looping:
        try:
            # Receive new data samples.
            samples = (yield)
            data_rows, column_names = process_samples(samples)

            # Upload the new data.
            num_rows = len(data_rows)
            if num_rows > 0:
                try:
                    blink_status.frequency = 30
                    response = fusion_tables.fusion_table.add_rows(service, tableId, data_rows)
                    blink_status.frequency = 0
                except fusion_tables.errors.Who8MyGoogleError as e:
                    blink_status.frequency = 0
                    print('Error caught: %s' % e.message)

                # Postprocess.
                key = 'numRowsReceived'
                if key in response:
                    num_uploaded = int(response[key])

                    # Everything worked OK?
                    if num_uploaded != num_rows:
                        print('Error: Problem uploading data: num_uploaded != num_rows: %s, %s' %
                              (num_uploaded, num_rows))
                        blink_status.frequency = 2

                else:
                    print('Error: Problem uploading data: %s' % response)
                    blink_status.frequency = 2

        except GeneratorExit:
            print('Data uploader: GeneratorExit')
            keep_looping = False

    # Stop the blinker.
    blink_status.frequency = 0
    blink_status.stop()

    # Done.


if __name__ == '__main__':
    pass
