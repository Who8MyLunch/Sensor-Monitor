
from __future__ import division, print_function, unicode_literals

import os

import numpy as np

import data_io as io

import who8mygoogle
import who8mygoogle.fusion_table as fusion_table
import who8mygoogle.authorize as authorize

import errors


# Static stuff.
master_table_id = '1rT2vCtaeiR9gO3k9n-DrKEPbvB54HKEhhGu2jNs'

# column_types = [['Kind',        fusion_table.TYPE_STRING],
                # ['Time',        fusion_table.TYPE_DATETIME],
                # ['Temperature', fusion_table.TYPE_NUMBER],
                # ['Humidity',    fusion_table.TYPE_NUMBER],
                # ['Tf_std',      fusion_table.TYPE_NUMBER],
                # ['RH_std',      fusion_table.TYPE_NUMBER]]


##################3


def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p


def get_api_service():
    """
    Establish credentials and retrieve API service object.
    """
    fname_client = 'client_secrets.json'
    api_name = 'fusiontables'
    
    path_data = os.path.join(path_to_module(), 'data')
    path_credentials = os.path.join(path_to_module(), 'credentials')

    f = os.path.join(path_credentials, fname_client)
    credentials = authorize.build_credentials(f, api_name)
    service = authorize.build_service(api_name, credentials)

    # Done.
    return service



def get():
    service = get_api_service()

    query_service = service.query()
    
    # sql = 'SELECT ROWID FROM %s' % master_table_id
    # request = query_service.sql(sql=sql)
    # try:
        # sql_results = request.execute()
    # except apiclient.errors.HttpError as e:
        # content = json.loads(e.content)
        # domain = content['error']['errors'][0]['domain']
        # message = content['error']['errors'][0]['message']
        # raise errors.Who8MyRPiError(domain + ': ' + message)
    # try:
        # num_rows = len(sql_results['rows'])
    # except KeyError:
        # num_rows = 0
    # if num_rows == 0:
        # raise errors.Who8MyRPiError('Master table invalid number of rows: %d' % num_rows)
    # # Get column names.
    # col_names = fusion_table.get_column_names(service, master_table_id)

    # Get the most recent row of config data.
    num_rows_req = 1
    my_query = 'SELECT * FROM ' + master_table_id + ' ORDER BY Time DESC LIMIT ' + str(num_rows_req)
    
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
    
    info = {}
    for k, v in zip(names, row):
        info[k] = v
    
    # Done.
    return info



def set(info):
    # https://developers.google.com/fusiontables/docs/v1/using#updateRow

    service = get_api_service()
    
    # Get column names.
    col_names = fusion_table.get_column_names(service, master_table_id)

    row = []
    for k in col_names:
        if not k in info:
            raise ValueError('Expected key not found in supplied info: %s' % k)
            
        row.append(info[k])
    
    rows_data = [row]
    fusion_table.add_rows(service, master_table_id, rows_data)
    

if __name__ == '__main__':
    """
    Run some examples.
    """
    print('a')
    val = get()
    print('b')
    
    print(val)



