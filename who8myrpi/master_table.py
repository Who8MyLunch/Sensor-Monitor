
from __future__ import division, print_function, unicode_literals

import os
import time

import numpy as np

import who8mygoogle
import who8mygoogle.fusion_table as fusion_table
import who8mygoogle.authorize as authorize
import apiclient.errors
import apiclient.http

import utility
import errors


#######################################################


def path_to_module():
    p = os.path.dirname(os.path.abspath(__file__))
    return p

#######################################################


def get_api_service():
    """
    Establish credentials and retrieve API service object.
    """
    fname_client = 'client_secrets.json'
    api_name = 'fusiontables'

    path_credentials = os.path.join(path_to_module(), 'credentials')

    f = os.path.join(path_credentials, fname_client)
    credentials = authorize.build_credentials(f, api_name)
    service = authorize.build_service(api_name, credentials)

    # Done.
    return service



def get(info_config):
    """
    Retrieve current data from master config table.
    """

    service = get_api_service()

    query_service = service.query()

    # Get the most recent row of config data.
    num_rows_req = 1
    my_query = 'SELECT * FROM ' + info_config['master_table_id'] + ' ORDER BY Time DESC LIMIT ' + str(num_rows_req)

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
        info_data[k] = v

    # Done.
    return info_data

    

def _make_master_row(info_config, data_table_id):
    # Set time stamp for new data.
    time_stamp = utility.pretty_timestamp(time.time())

    # Build new row structure.
    row = {}
    row['Time'] = time_stamp
    row['Experiment Name'] = info_config['experiment_name']
    row['Data Table ID'] = data_table_id
    row['Pins Data'] = str(info_config['pins_data']).replace('[', '').replace(']', '')
    row['Pin OK'] = info_config['pin_ok']
    row['Pin Error'] = info_config['pin_err']
    row['Pin Power'] = info_config['pin_power']
    row['Power Cycle'] = info_config['power_cycle_interval']

    return row



def set(info_config, data_table_id):
    """
    Upload updated master information.
    # https://developers.google.com/fusiontables/docs/v1/using#updateRow
    """

    info_data = _make_master_row(info_config, data_table_id)
    
    # Get column names.
    service = get_api_service()
    col_names = fusion_table.get_column_names(service, info_config['master_table_id'])

    row = []
    for k in col_names:
        if not k in info_data:
            raise ValueError('Expected key not found in supplied info: %s' % k)

        row.append(info_data[k])

    rows_data = [row]
    response = fusion_table.add_rows(service, info_config['master_table_id'], rows_data)


    if int(response['numRowsReceived']) != 1:
        raise Who8MyRPiError('Problem uploading new data to master table.')

    # Done.



if __name__ == '__main__':
    """
    Run some examples.
    """
    print('A little example')

    val = get()
    print(val)

    data_table_id = 'this is an ID?'
    val_new = set(data_table_id)

    print(val_new)


