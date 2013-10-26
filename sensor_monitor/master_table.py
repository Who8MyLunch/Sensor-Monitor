
from __future__ import division, print_function, unicode_literals

import os

import simplejson as json

import who8mygoogle.fusion_tables as fusion_tables

import apiclient.errors
import apiclient.http

import data_io
import errors

import argparse
# import oauth2client.client
# import oauth2client.file
import oauth2client.tools

#################################################


def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p

#################################################

_FNAME_CLIENT_SECRETS = 'client_secrets.json'
_FOLDER_CREDENTIALS = 'credentials'


def build_config():
    """
    This is a helper function to assemble required config data.
    """
    fname = 'config_data.yml'

    # parser is here to play nice with Google's stuff using the flags variable.
    parser = argparse.ArgumentParser(description="authorize",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     parents=[oauth2client.tools.argparser])
    flags = parser.parse_args()

    info, meta = data_io.read(fname)

    return info, flags


def get(info_config, flags=None):
    """
    Retrieve current data from master config table.
    """

    api_name = 'fusiontables'

    path_credentials = os.path.join(path_to_module(), _FOLDER_CREDENTIALS)
    if not os.path.isdir(path_credentials):
        os.makedirs(path_credentials)

    # Fetch main service object.
    f = os.path.join(path_credentials, _FNAME_CLIENT_SECRETS)
    service = fusion_tables.authorize.get_api_service(f, api_name, flags)

    # Get a query object.
    query_service = service.query()

    # Get the most recent row of config data.
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


def get_current_table_id():
    """
    Get from master table the ID for current working table.
    """

    info, flags = build_config()
    val = get(info, flags)

    table_id = val['data_table_id']

    return table_id

#################################################


if __name__ == '__main__':
    """
    Print info from Master Table.

    Also good for debugging connection to Google via API.
    """

    # fname = 'config_data.yml'
    # parser = argparse.ArgumentParser(description="authorize",
    #                                  formatter_class=argparse.RawDescriptionHelpFormatter,
    #                                  parents=[oauth2client.tools.argparser])
    # flags = parser.parse_args()
    # info_config, meta = data_io.read(fname)

    info, flags = build_config()
    val = get(info, flags)

    print()
    for k, v in val.items():
        print('{:s}: {:s}'.format(k, v))

    # Done.
