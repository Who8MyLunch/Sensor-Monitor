
from __future__ import division, print_function, unicode_literals

import os
import argparse

import who8mygoogle.fusion_tables as fusion_tables
import master_table
import utility

import oauth2client.tools


#################################################
# Helpers.
def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p

#################################################

_FNAME_CLIENT_SECRETS = 'client_secrets.json'
_FOLDER_CREDENTIALS = 'credentials'


def fetch_data(my_query):
    """
    Fetch the data from Google Fusion Table.
    The query string must contain the ID for the Fusion Table.
    """

    # Parser is here to play nice with Google's stuff using the flags variable.
    parser = argparse.ArgumentParser(description="Data Downloader",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     parents=[oauth2client.tools.argparser])
    flags = parser.parse_args()

    # Connect to Fusion Table using functions from package Who8MyGoogle.
    api_name = 'fusiontables'

    path_credentials = os.path.join(path_to_module(), _FOLDER_CREDENTIALS)
    f = os.path.join(path_credentials, _FNAME_CLIENT_SECRETS)

    # Service object.
    service = fusion_tables.authorize.get_api_service(f, api_name, flags)

    # Get a query object, https://developers.google.com/fusiontables/docs/v1/sql-reference
    query_service = service.query()

    # Perform request.
    request = query_service.sql(sql=my_query)
    sql_results = request.execute()

    # Pull out just the rows.
    data = sql_results['rows']

    return data


def data_recent(table_id, num_rows=10):
    """
    Download most recent data from a Google Fusion Table.
    Default to just fetching 10 rows.
    """
    my_query = 'SELECT * FROM {:s} ORDER BY Seconds DESC LIMIT {:d}'.format(table_id, num_rows)
    return fetch_data(my_query)


def data_between(table_id, seconds_start, seconds_end=None):
    """
    Download data spanning time range from a Google Fusion Table.
    If end time not specified then fetch up to most recent.
    """
    if seconds_end:
        conditions = 'Seconds >= {:.1f} AND Seconds <= {:.1f}'.format(seconds_start, seconds_end)
    else:
        conditions = 'Seconds >= {:.1f}'.format(seconds_start)

    # All data between start and stop times.
    my_query = 'SELECT * FROM {:s} WHERE {:s} ORDER BY Seconds ASC'.format(table_id, conditions)

    return fetch_data(my_query)

#################################################


if __name__ == '__main__':
    """
    Example use.
    """

    table_id = master_table.get_current_table_id()
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
