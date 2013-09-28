
from __future__ import division, print_function, unicode_literals

import os
# import datetime
# import time
import argparse

# import simplejson as json
# import numpy as np
# import data_io

import who8mygoogle.fusion_tables as fusion_tables
import master_table
import utility

import oauth2client.tools
# import apiclient.errors
# import apiclient.http


#################################################
# Helpers.
def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p

#################################################


def data_fetch(my_query):
    """
    Fetch the data from Google.
    """
    print('Query Data Table')

    # Parser is here to play nice with Google's stuff using the flags variable.
    parser = argparse.ArgumentParser(description="Data Downloader",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     parents=[oauth2client.tools.argparser])
    flags = parser.parse_args()

    # Connect to Fusion Table using functions from package Who8MyGoogle.
    api_name = 'fusiontables'

    fname_client_secrets = 'client_secrets.json'
    path_credentials = os.path.join(path_to_module(), 'credentials')
    f = os.path.join(path_credentials, fname_client_secrets)

    # Service object.
    service = fusion_tables.authorize.get_api_service(f, api_name, flags)

    # Get a query object, https://developers.google.com/fusiontables/docs/v1/sql-reference
    query_service = service.query()

    # Perform request.
    request = query_service.sql(sql=my_query)
    sql_results = request.execute()

    # Done.
    return sql_results['rows']


def data_recent(table_id, num_rows=10):
    """
    Download some data from a Google Fusion Table.
    """

    # Most recent data samples.
    my_query = 'SELECT * FROM {:s} ORDER BY Seconds DESC LIMIT {:d}'.format(table_id, num_rows)

    return data_fetch(my_query)

    # query_service = service.query()
    # request = query_service.sql(sql=my_query)
    # try:
    #     sql_results = request.execute()
    # except Exception as e:
    #     raise e
    # for r in sql_results['rows']:
    #     print(r)


def data_between(table_id, seconds_start, seconds_end=None):
    """
    Download some data from a Google Fusion Table.
    """

    if seconds_end:
        conditions = 'Seconds >= {:.1f} AND Seconds <= {:.1f}'.format(seconds_start, seconds_end)
    else:
        conditions = 'Seconds >= {:.1f}'.format(seconds_start)

    # All data between start and stop times.
    my_query = 'SELECT * FROM {:s} WHERE {:s} ORDER BY Seconds ASC'.format(table_id, conditions)

    return data_fetch(my_query)


if __name__ == '__main__':
    """
    Download data from current fusion table.
    """
    # parser is here to play nice with Google's stuff using the flags variable.
    # parser = argparse.ArgumentParser(description="Data Downloader",
    #                                  formatter_class=argparse.RawDescriptionHelpFormatter,
    #                                  parents=[oauth2client.tools.argparser])
    # flags = parser.parse_args()

    # # Read config file for Master Table information.
    # fname = 'config_data.yml'
    # info_config, meta = data_io.read(fname)

    info, flags = master_table.build_config()
    val = master_table.get(info, flags)

    table_id = val['data_table_id']

    print('Table ID: {:s}'.format(table_id))

    # Start and end time.
    year = 2013
    month = 9
    day = 18
    hour = 19
    minute = 0
    time_start = utility.timestamp_seconds(year, month, day, hour, minute)

    # hour = 20
    # minute = 30
    # time_end = utility.timestamp_seconds(year, month, day, hour, minute)

    data = data_between(table_id, time_start)

    # Done.
