
from __future__ import division, print_function, unicode_literals

import os
import shutil
import glob
import datetime
import time

import data_io as io

import who8mygoogle.fusion_table as fusion_table
import who8mygoogle.authorize as authorize

###################################
# Helpers.
def reformat_float(value):
    value = float(value)
    value_pretty = '%.3f' % value

    return value_pretty

    
    
def reformat_timestamp(seconds):
    if type(seconds) == str or type(seconds) == unicode:
        seconds = float(seconds)

    d = datetime.datetime.utcfromtimestamp(seconds)
    time_stamp = d.strftime('%Y-%m-%d %H:%M:%S')

    return time_stamp

    
##########################################    


def load_files(files):
    """
    Load a number of data files, concatenate into single list of rows.
    """
    data = []
    for f in files:
        rows, header = io.read(f)

        for r in rows:
            # Reformat some numbers.
            sec = r[6]
            stamp = reformat_timestamp(sec)
            r[6] = stamp
            
            for k in [1, 2, 3, 4]:
                v = r[k]
                v = reformat_float(v)
                r[k] = v
                
            data.append(r)

    # Done.
    return data, header


##############################
# Setup.
experiment_name = 'Testing B | Six Sensors'

column_types = [['pin',     fusion_table.TYPE_NUMBER],
                ['RH_avg',  fusion_table.TYPE_NUMBER],
                ['RH_std',  fusion_table.TYPE_NUMBER],
                ['Tf_avg',  fusion_table.TYPE_NUMBER],
                ['Tf_std',  fusion_table.TYPE_NUMBER],
                ['Samples', fusion_table.TYPE_NUMBER],
                ['Time',    fusion_table.TYPE_DATETIME]]

##
num_batch = 100  # number of files per batch
time_poll = 5.   # seconds

path_base = os.path.curdir
folder_data = 'data'
folder_archive = 'archive'

folder_credentials = 'credentials'

fname_client = 'client_secrets.json'
api_name = 'fusiontables'

##############################
# Do it.
path_data = os.path.join(os.path.abspath(path_base), folder_data)
path_archive = os.path.join(path_data, folder_archive)

path_credentials = os.path.join(os.path.abspath(path_base), folder_credentials)

# Setup Google API credentials.
print('Establish credentials...')

f = os.path.join(path_credentials, fname_client)
credentials = authorize.build_credentials(f, api_name)
service = authorize.build_service(api_name, credentials)

print('Fetch Fusion Table...')
tableId = fusion_table.fetch_table(service, experiment_name, column_types)

print('Table ID: %s' % tableId)


# Main processing loop.
try:
    print('Working...')
    
    pattern = os.path.join(path_data, '*.csv')
    ok = True
    
    while ok:
        # List of candidate files.
        files = glob.glob(pattern)
        files.sort()

        # got more than one file?
        if len(files) > 1:
            # Leave one behind.
            files = files[:-1]
            files = files[:num_batch]
            num_files = len(files)

            print('Reading files: %d' % num_files)

            data, header = load_files(files)
            num_rows = len(data)
            
            response = fusion_table.add_rows(service, tableId, data)

            key = 'numRowsReceived'
            if key in response:
                num_uploaded = int(response[key])

                # Everything worked OK?
                if num_uploaded == num_rows:
                    # Move processed files to archive.
                    for f in files:
                        shutil.move(f, path_archive)
                else:
                    raise Exception('Problem uploading data: %s' % response)

            else:
                raise Exception('Problem uploading data: %s' % response)
                
        # Pause.
        time.sleep(time_poll)

        # Repeat.


except KeyboardInterrupt:
    # End it all when user hits ctrl-c.
    print()
    print()
    print('User stop!')


print('Done')
