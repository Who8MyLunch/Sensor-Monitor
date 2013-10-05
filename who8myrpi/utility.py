
from __future__ import division, print_function, unicode_literals

import subprocess
import shlex
import datetime
import calendar

import pytz
import string


def valid_filename(fname_in):
    """
    Take a string and return a valid filename constructed from the string.
    Uses a whitelist approach: any characters not present in valid_chars are
    removed. Also spaces are replaced with underscores.

    Note: this method may produce invalid filenames such as ``, `.` or `..`
    When I use this method I prepend a date string like '2009_01_15_19_46_32_'
    and append a file extension like '.txt', so I avoid the potential of using
    an invalid filename.
    """
    valid_chars = '-_.() %s%s' % (string.ascii_letters, string.digits)

    fname_out = ''.join(c for c in fname_in if c in valid_chars)
    # fname_out = fname_out.replace(' ','_') # don't like spaces in filenames.

    # Done.
    return fname_out


def run_cmd(cmd):
    cmd = shlex.split(cmd)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    proc.wait()

    # Done.
    return stdout, stderr


# def network_reset():
#     cmd = 'ifdown eth0'
#     stdout, stderr = run_cmd(cmd)
#     if stderr != '':
#         print('utility.network_reset A: uh oh!')
#     time.sleep(5)
#     cmd = 'ifup eth0'
#     stdout, stderr = run_cmd(cmd)
#     if stderr != '':
#         print('utility.network_reset B: uh oh!')


# Timezones.
tz_UTC = pytz.timezone('UTC')
tz_LAX = pytz.timezone('America/Los_Angeles')


def datetime_seconds(seconds_utc, tz='US/Pacific'):
    """
    Output a date_time object computed from supplied input UTC seconds.

    tz: optional timezone information in format known by pytz.
        e.g. tz='UTC' | 'US/Eastern' | 'US/Pacific' | 'America/Los Angeles'
    tz can also be a pytz timezone instance.
    """
    if isinstance(seconds_utc, basestring):
        seconds_utc = float(seconds_utc)

    dt_UTC = datetime.datetime.fromtimestamp(seconds_utc, tz_UTC)

    if tz:
        if isinstance(tz, basestring):
            tz_user = pytz.timezone(tz)
            dt_user = dt_UTC.astimezone(tz_user)
        else:
            dt_user = dt_UTC.astimezone(tz)
    else:
        dt_user = dt_UTC

    return dt_user


def pretty_timestamp(seconds_utc, fmt='%Y-%m-%d %H:%M:%S'):
    """
    Make a pretty timestamp from supplied UTC seconds.
    default fmt = '%Y-%m-%d %H:%M:%S'
    """
    dt_LAX = datetime_seconds(seconds_utc)
    time_stamp = dt_LAX.strftime(fmt)

    return time_stamp


def timestamp_seconds(year, month, day, hour=0, minute=0, seconds=0):
    """
    Compute UTC seconds from time/date specified in LAX timesone..
    """
    dt_LAX = tz_LAX.localize(datetime.datetime(year, month, day, hour, minute, seconds, 0))
    dt_UTC = dt_LAX.astimezone(tz_UTC)

    time_seconds = calendar.timegm(dt_UTC.utctimetuple())

    return time_seconds
