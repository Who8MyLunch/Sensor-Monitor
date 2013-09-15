
from __future__ import division, print_function, unicode_literals

import os
import datetime
import time

import numpy as np
import data_io

import who8mygoogle.fusion_tables as fusion_tables
import master_table

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

    tableId = fusion_tables.fusion_table.fetch_table(service, table_name, verbose=True)

    # Done.
    return service, tableId



def download_data(service, tableId):
    """
    Download some data from a Google Fusion Table.
    """



    keep_looping = True
    while keep_looping:
        try:
            # Receive new data samples.
            samples = (yield)
            data_rows, column_names = process_samples(samples)

            # Upload the new data.
            num_rows = len(data_rows)
            if num_rows > 0:
                blink_status.frequency = 30
                try:
                    response = fusion_tables.fusion_table.add_rows(service, tableId, data_rows)
                except fusion_tables.errors.Who8MyGoogleError as e:
                    print('Error caught: %s' % e.message)

                blink_status.frequency = 0

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
        except Exception as e:
            blink_status.stop()
            raise e

    # Stop the blinker.
    blink_status.frequency = 0
    blink_status.stop()

    # Done.


if __name__ == '__main__':
    """
    Download data from current fusion table.
    """
    import argparse
    import oauth2client.tools


    # parser is here to play nice with Google's stuff using the flags variable.
    parser = argparse.ArgumentParser(description="Data Downloader",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     parents=[oauth2client.tools.argparser])
    flags = parser.parse_args()

    # Read config file for Master Table information.
    fname = 'config_data.yml'
    info_config, meta = data_io.read(fname)

    val = master_table.get(info_config, flags)

    service = master_table.get_api_service(flags)
    fusion_tables.fusion_table.display_existing_tables(service)


    # print()
    # for k, v in val.items():
    #     print('{:s}: {:s}'.format(k, v))

    # Done.
