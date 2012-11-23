
from __future__ import division, print_function, unicode_literals

import os
import shutil
import glob
import datetime
import time

import numpy as np
import pytz

import data_io as io

import who8mygoogle.fusion_table as fusion_table
import who8mygoogle.authorize as authorize

###################################
# Helpers.
#

def reformat_timestamp(seconds):
    if type(seconds) == str or type(seconds) == unicode:
        seconds = float(seconds)
        
    tz_UTC = pytz.timezone('UTC')
    dt_UTC = datetime.datetime.fromtimestamp(seconds, pytz.utc)
    
    tz_LAX = pytz.timezone('America/Los_Angeles')
    dt_LAX = dt_UTC.astimezone(tz_LAX)
    
    fmt = '%Y-%m-%d %H:%M:%S %Z%z'
    time_stamp = dt_LAX.strftime(fmt)

    # Done.
    return time_stamp


##########################################

def process_data(data_sens, header_sens):
    """
    Interpret recorded input data.
    row = pin, RH_avg, RH_std, Tf_avg, Tf_std, Samples, Time
    One pin per row.

    Generate output data appropriate for upload to Fusion Table.
    row = Time, RH_avg, RH_std, Tf_avg, Tf_std, Quality
    """
    ix_pin = 0
    ix_RH_avg = 1
    ix_RH_std = 2
    ix_Tf_avg = 3
    ix_Tf_std = 4
    ix_Samples = 5
    ix_Time = 6

    # Data recorded during sensors' sampling interval.
    times = [row[ix_Time] for row in data_sens]
    times = [reformat_timestamp(t) for t in times]

    Tf_time_avg = np.asarray( [float(row[ix_Tf_avg]) for row in data_sens] )
    RH_time_avg = np.asarray( [float(row[ix_RH_avg]) for row in data_sens] )

    samples = np.asarray( [int(row[ix_Samples]) for row in data_sens])

    # RH_time_std = [row[ix_RH_std] for row in data_sens]
    # Tf_time_std = [row[ix_Tf_std] for row in data_sens]

    # Interpret the data.
    time_data = times[0]    # assume all time values are the same.

    Tf_data = np.round( np.mean(Tf_time_avg), 2)
    RH_data = np.round( np.mean(RH_time_avg), 2)

    Tf_std_data = np.round( np.std(Tf_time_avg), 2)
    RH_std_data = np.round( np.std(RH_time_avg), 2)

    samples_high = np.max(samples)
    samples_med = np.median(samples)
    samples_low = np.min(samples)

    quality_A = samples_med / 15.  # maximum numberof samples is around 14 - 15.
    quality_B = samples_low / 15. # maximum numberof samples is around 14 - 15.

    # Finish.
    data_numbers = [Tf_data, RH_data, Tf_std_data, RH_std_data, quality_A, quality_B]
    data_numbers = ['%.2f' % val for val in data_numbers]

    data_out = [time_data]
    data_out.extend(data_numbers)

    header_out = ['Time', 'Temperature', 'Humidity', 'Tf_std', 'RH_std', 'Quality_A', 'Quality_B']

    # Done.
    return data_out, header_out



def load_data_files(files):
    """
    Load a number of data files, concatenate into single list of rows.
    """
    data_proc = []
    num_rows = 0
    for f in files:
        rows_sens, header_sens = io.read(f)
        num_rows += len(rows_sens)

        row_proc, header_proc = process_data(rows_sens, header_sens)

        data_proc.append(row_proc)

    # Done.
    return data_proc, header_proc, num_rows


####################

def build_summary(num_rows, info_summary=None):
    """
    Summary of collected data.
    """
    if info_summary is None:
        info_summary = {}

    key = 'num_uploaded'
    if not key in info_summary:
        info_summary[key] = 0

    info_summary[key] += num_rows

    # Done.
    return info_summary



def pretty_status(time_now, info_summary):
    """
    Display pretty status update.
    """
    d = datetime.datetime.utcfromtimestamp(time_now)
    time_stamp = d.strftime('%Y-%m-%d %H:%M:%S')
    
    key = 'num_uploaded'
    num_uploaded_str = '%3d' % info_summary[key]

    msg = '%s || %s' % (time_stamp, num_uploaded_str)
    print(msg)

    # Done.

#######################################3

# Static stuff.
column_types = [['Time',        fusion_table.TYPE_DATETIME],
                ['Temperature', fusion_table.TYPE_NUMBER],
                ['Humidity',    fusion_table.TYPE_NUMBER],
                ['Tf_std',      fusion_table.TYPE_NUMBER],
                ['RH_std',      fusion_table.TYPE_NUMBER],
                ['Quality_A',     fusion_table.TYPE_NUMBER],
                ['Quality_B',     fusion_table.TYPE_NUMBER]]

fname_client = 'client_secrets.json'
api_name = 'fusiontables'

#####

def acquire_api_service(experiment_name, path_credentials):
    """
    Establish credentials and retrieve API service object.
    """

    f = os.path.join(path_credentials, fname_client)
    credentials = authorize.build_credentials(f, api_name)
    service = authorize.build_service(api_name, credentials)

    tableId = fusion_table.fetch_table(service, experiment_name, column_types)

    # Done.
    return service, tableId



def upload_data(service, tableId, path_data, num_batch=100, time_poll=5., status_interval=60*10):
    """
    Main work function.
    
    time_poll: seconds
    status_interval: seconds
    """

    pattern_data = os.path.join(path_data, '201?-??-??', '*.csv')
    folder_archive = 'archive'

    # Main processing loop.
    time_zero = time.time()
    info_summary = None

    try:
        ok = True

        while ok:
            # List of candidate files.
            files = glob.glob(pattern_data)
            files.sort()

            # Got some files?
            if len(files) > 0:
                time.sleep(0.01)
                
                files = files[:num_batch]
                num_files = len(files)

                data_proc, header_proc, num_rows_proc = load_data_files(files)
                num_rows = len(data_proc)

                response = fusion_table.add_rows(service, tableId, data_proc)

                info_summary = build_summary(num_rows_proc, info_summary)

                key = 'numRowsReceived'
                if key in response:
                    num_uploaded = int(response[key])

                    # Everything worked OK?
                    if num_uploaded == num_rows:
                        # Move processed files to archive.
                        for f in files:
                            path_archive = os.path.join(os.path.dirname(f), folder_archive)
                            if not os.path.isdir(path_archive):
                                os.mkdir(path_archive)

                            shutil.move(f, path_archive)
                    else:
                        raise Exception('Problem uploading data: %s' % response)

                else:
                    raise Exception('Problem uploading data: %s' % response)

            # Status update.
            time_now = time.time()
            time_elapsed = time_now - time_zero
            if time_elapsed > status_interval:
                # Status display.
                pretty_status(time_now, info_summary)

                # Reset.
                time_zero = time_now
                info_summary = None

            # Pause.
            time.sleep(time_poll)

            # Repeat.

    except KeyboardInterrupt:
        # End it all when user hits ctrl-c.
        print()
        print()
        print('User stop!')

    # Done.


if __name__ == '__main__':
    pass



