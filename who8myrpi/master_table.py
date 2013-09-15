
from __future__ import division, print_function, unicode_literals

import os
import time
import argparse

import simplejson as json
import numpy as np

import who8mygoogle.fusion_tables as fusion_tables

import apiclient.errors
import apiclient.http

import utility
import errors


#######################################################


def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p

#######################################################


def get_api_service(flags=None):
    """
    Establish credentials and retrieve API service object.
    """
    fname_client = 'client_secrets.json'
    api_name = 'fusiontables'

    path_credentials = os.path.join(path_to_module(), 'credentials')
    if not os.path.isdir(path_credentials):
        os.makedirs(path_credentials)

    f = os.path.join(path_credentials, fname_client)
    credentials = fusion_tables.authorize.build_credentials(f, api_name, flags)
    service = fusion_tables.authorize.build_service(api_name, credentials)

    # Done.
    return service



def get(info_config, flags):
    """
    Retrieve current data from master config table.
    """
    service = get_api_service(flags)
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



if __name__ == '__main__':
    """
    Print info from Master Table.

    Also good for debugging connection to Google via API.
    """
    import argparse
    import oauth2client.client
    import oauth2client.file
    import oauth2client.tools

    import data_io

    fname = 'config_data.yml'

    parser = argparse.ArgumentParser(description="authorize",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     parents=[oauth2client.tools.argparser])
    flags = parser.parse_args()

    info_config, meta = data_io.read(fname)

    val = get(info_config, flags)

    print()
    for k, v in val.items():
        print('{:s}: {:s}'.format(k, v))

    # Done.
