
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

    api_name = 'fusiontables'
    fname_client_secrets = 'client_secrets.json'

    path_credentials = os.path.join(path_to_module(), 'credentials')
    if not os.path.isdir(path_credentials):
        os.makedirs(path_credentials)

    # Fetch main service object.
    f = os.path.join(path_credentials, fname_client_secrets)
    service = fusion_tables.authorize.get_api_service(f, api_name, flags)

    # Get a query object.
    query_service = service.query()

    # Get the most recent row of config data.
    #num_rows_req = 1
    #my_query = 'SELECT * FROM ' + info_config['master_table_id'] + ' ORDER BY Time DESC LIMIT ' + \
    #           str(num_rows_req)

    my_query = 'SELECT * FROM ' + info_config['master_table_id'] + ' LIMIT 1'
    request = query_service.sql(sql=my_query)

    try:
        sql_results = request.execute()
    except apiclient.errors.HttpError as e:
        content = json.loads(e.content)
        domain = content['error']['errors'][0]['domain']
        message = content['error']['errors'][0]['message']

        raise errors.Who8MyRPiError(domain + ': ' + message)

    # Extract most recent row.
    names = sql_results['columns']
    row = sql_results['rows'][0]

    info_data = {}
    for k, v in zip(names, row):
        k = k.lower()
        k = '_'.join(k.split())
        info_data[k] = v

    # Done.
    return info_data



    # print()
    # for k, v in val.items():
    #     print('{:s}: {:s}'.format(k, v))

    # Done.
