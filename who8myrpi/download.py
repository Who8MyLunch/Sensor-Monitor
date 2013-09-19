
from __future__ import division, print_function, unicode_literals

import os
import datetime
import time

import numpy as np
import data_io

import who8mygoogle.fusion_tables as fusion_tables
import master_table
import utility

import simplejson as json
import apiclient.errors
import apiclient.http

#################################################

def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p


def download_data(service, tableId):
    """
    Download some data from a Google Fusion Table.
    """
    pass


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

    print('\nQuery Master Table')
    val = master_table.get(info_config, flags)

    print()
    keys = ['experiment_name', 'data_table_id']
    for k in keys:
        v = val[k]
        print('{:s}: {:s}'.format(k, v))

    table_id = val['data_table_id']


    # Connect to Fusion Table using functions from package Who8MyGoogle.
    print('\nQuery Data Table')

    api_name = 'fusiontables'
    fname_client_secrets = 'client_secrets.json'

    path_credentials = os.path.join(path_to_module(), 'credentials')
    f = os.path.join(path_credentials, fname_client_secrets)

    service = fusion_tables.authorize.get_api_service(f, api_name, flags)

    # Display column names.
    # names = fusion_tables.fusion_table.get_column_names(service, table_id)
    # print(names)

    # Get a query object.
    # https://developers.google.com/fusiontables/docs/v1/sql-reference
    query_service = service.query()

    # Start & end time.
    year = 2013
    month = 9
    day = 18
    hour = 19
    minute = 0
    time_start = utility.timestamp_seconds(year, month, day, hour, minute)

    hour = 20
    minute = 30
    time_end = utility.timestamp_seconds(year, month, day, hour, minute)

    assert(time_end - time_start > 0)

    num_rows_req = 10
    conditions = 'Seconds >= {:.1f} AND Seconds <= {:.1f}'.format(time_start, time_end)

    # All data between start and stop times.
    # my_query = 'SELECT * FROM {:s} WHERE {:s} ORDER BY Seconds ASC'.format(table_id, conditions)

    # Most recent data samples.
    num_rows_req = 5
    my_query = 'SELECT * FROM {:s} ORDER BY Seconds DESC LIMIT {:d}'.format(table_id, num_rows_req)

    request = query_service.sql(sql=my_query)

    try:
        sql_results = request.execute()
    except Exception as e:
        raise e

    for r in sql_results['rows']:
        print(r)

