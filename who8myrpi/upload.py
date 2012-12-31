
from __future__ import division, print_function, unicode_literals

import os
import shutil
import glob
import datetime
import time

import numpy as np

import data_io as io

import who8mygoogle
import who8mygoogle.fusion_table as fusion_table
import who8mygoogle.authorize as authorize

import utility
import errors


##########################################

# def process_data_OLD(data_sens, header_sens):
    # """
    # Interpret recorded input data.
    # row = pin, RH_avg, RH_std, Tf_avg, Tf_std, Samples, Time
    # One pin per row.
    # Generate output data appropriate for upload to Fusion Table.
    # row = Time, RH_avg, RH_std, Tf_avg, Tf_std, Quality
    # """
    # ix_pin = 0
    # ix_RH_avg = 1
    # ix_RH_std = 2
    # ix_Tf_avg = 3
    # ix_Tf_std = 4
    # ix_Samples = 5
    # ix_Time = 6
    # # Data recorded during sensors' sampling interval.
    # times = [row[ix_Time] for row in data_sens]
    # times = [utility.pretty_timestamp(t) for t in times]
    # Tf_time_avg = np.asarray( [float(row[ix_Tf_avg]) for row in data_sens] )
    # RH_time_avg = np.asarray( [float(row[ix_RH_avg]) for row in data_sens] )
    # samples = np.asarray( [int(row[ix_Samples]) for row in data_sens])
    # # RH_time_std = [row[ix_RH_std] for row in data_sens]
    # # Tf_time_std = [row[ix_Tf_std] for row in data_sens]
    # # Interpret the data.
    # time_data = times[0]    # assume all time values are the same.
    # Tf_data = np.round( np.median(Tf_time_avg), 2)
    # RH_data = np.round( np.median(RH_time_avg), 2)
    # Tf_std_data = np.round( np.std(Tf_time_avg), 2)
    # RH_std_data = np.round( np.std(RH_time_avg), 2)
    # samples_high = np.max(samples)
    # samples_med = np.median(samples)
    # samples_low = np.min(samples)
    # quality_A = samples_med / 15.  # maximum numberof samples is around 14 - 15.
    # quality_B = samples_low / 15. # maximum numberof samples is around 14 - 15.
    # # Finish.
    # data_numbers = [Tf_data, RH_data, Tf_std_data, RH_std_data, quality_A, quality_B]
    # data_numbers = ['%.2f' % val for val in data_numbers]
    # data_out = [time_data]
    # data_out.extend(data_numbers)
    # header_out = ['Time', 'Temperature', 'Humidity', 'Tf_std', 'RH_std', 'Quality_A', 'Quality_B']
    # # Done.
    # return data_out, header_out
# def build_summary(num_rows, info_summary=None):
    # """
    # Summary of collected data.
    # """
    # if info_summary is None:
        # info_summary = {}
    # key = 'num_uploaded'
    # if not key in info_summary:
        # info_summary[key] = 0
    # info_summary[key] += num_rows
    # # Done.
    # return info_summary
# def pretty_status(time_now, info_summary=None):
    # """
    # Display pretty status update.
    # """
    # if info_summary is None:
        # info_summary = {'num_uploaded': 0}
    # d = datetime.datetime.utcfromtimestamp(time_now)
    # time_stamp = d.strftime('%Y-%m-%d %H:%M:%S')
    # key = 'num_uploaded'
    # num_uploaded_str = '%3d' % info_summary[key]
    # msg = '%s || %s' % (time_stamp, num_uploaded_str)
    # print(msg)
    # # Done.


    
def load_data_files(files):
    """
    Load a number of data files, concatenate into single list of rows.

    column_types = [['Time',        fusion_table.TYPE_DATETIME],
                    ['Kind',        fusion_table.TYPE_STRING],
                    ['Pin',         fusion_table.TYPE_NUMBER],
                    ['Temperature', fusion_table.TYPE_NUMBER],
                    ['Humidity',    fusion_table.TYPE_NUMBER]]

    -   time_stamp: 1355600730.603534
        kind: sample
        pin: 23
        Tf: 54.32
        RH: 65.7
    """
    fields_to_columns = ['seconds',
                         'kind',
                         'pin',
                         'Tf',
                         'RH']
    data_rows = []
    for f in files:
        data_samples, meta = io.read(f)

        if data_samples is None:        
            print('no data in file: %s' % os.path.basename(f))
        else:
            for d in data_samples:
                row = [d[n] for n in fields_to_columns]

                seconds = row[0]
                time_stamp = utility.pretty_timestamp(seconds)
                row.insert(0, time_stamp)

                data_rows.append(row)

    column_names = fields_to_columns
    column_names.insert(0, 'DateTime')
    
    # Done.
    return data_rows, column_names


# Static stuff.
column_types = [['DateTime',    fusion_table.TYPE_DATETIME],
                ['Seconds',     fusion_table.TYPE_NUMBER],
                ['Kind',        fusion_table.TYPE_STRING],
                ['Pin',         fusion_table.TYPE_NUMBER],
                ['Temperature', fusion_table.TYPE_NUMBER],
                ['Humidity',    fusion_table.TYPE_NUMBER]]

fname_client = 'client_secrets.json'
api_name = 'fusiontables'

#####

def connect_table(table_name, path_credentials):
    """
    Establish credentials and retrieve API service object.
    """

    f = os.path.join(path_credentials, fname_client)
    credentials = authorize.build_credentials(f, api_name)
    service = authorize.build_service(api_name, credentials)

    tableId = fusion_table.fetch_table(service, table_name, column_types)

    # Done.
    return service, tableId



def upload_data(service, tableId, path_data):
    """
    Main work function.

    time_poll: seconds
    status_interval: seconds
    """

    # Setup.
    num_batch = 100
    time_poll = 5

    pattern_data = os.path.join(path_data, 'data-201*.yml')
    folder_archive = 'archive'

    # Main processing loop.
    time_zero = time.time()
    info_summary = None

    try:
        keep_looping = True

        while keep_looping:
            time_zero = time.time()
            
            # List of candidate files.
            files = glob.glob(pattern_data)
            files.sort()

            # Got some files?
            if len(files) > 0:

                time.sleep(0.01)  # small sleep to ensure that found files are fully written to disk.

                files = files[:num_batch]
                num_files = len(files)

                data_rows, column_names = load_data_files(files)
                num_rows = len(data_rows)

                # Upload the new data.
                if num_rows > 0:
                    response = fusion_table.add_rows(service, tableId, data_rows)

                    # Postprocess.
                    key = 'numRowsReceived'
                    if key in response:
                        num_uploaded = int(response[key])

                        # Everything worked OK?
                        if num_uploaded == num_rows:
                            print('uploaded: %d' % num_uploaded)
                            
                            # Move processed files to archive.
                            for f in files:
                                path_archive = os.path.join(os.path.dirname(f), folder_archive)
                                if not os.path.isdir(path_archive):
                                    os.mkdir(path_archive)

                                shutil.move(f, path_archive)
                        else:
                            raise errors.Who8MyRPiError('Problem uploading data since num_uploaded != num_rows: %s, %s' % (num_uploaded, num_rows))

                    else:
                        raise errors.Who8MyRPiError('Problem uploading data: %s' % response)

            # Wait a bit before searching for and uploading more data.
            time_delta = time_poll - (time.time() - time_zero)   

            if time_delta > 0:
                # print('wait: %.2f' % time_delta)
                time.sleep(time_delta)

            # Repeat.

            
    except who8mygoogle.Who8MyGoogleError as e:
        print('Caught error: %s' % e)
        return -1

    except errors.Who8MyRPiError as e:
        print('Caught error: %s' % e)
        return -1

    except KeyboardInterrupt:
        # End it all when user hits ctrl-c.
        print()
        print('User stop!')

    # Done.
    if info_summary is None:
        val = 0
    else:
        val = info_summary['num_uploaded']

    return val


if __name__ == '__main__':
    pass



