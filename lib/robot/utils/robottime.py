#  Copyright 2008-2011 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import time

from normalizing import normalize
from misc import plural_or_not


def _get_timetuple(epoch_secs=None):
    if _CURRENT_TIME:
        return _CURRENT_TIME
    if epoch_secs is None:  # can also be 0 (at least in unit tests)
        epoch_secs = time.time()
    secs, millis = _float_secs_to_secs_and_millis(epoch_secs)
    timetuple = time.localtime(secs)[:6]  # from year to secs
    return timetuple + (millis,)

def _float_secs_to_secs_and_millis(secs):
    isecs = int(secs)
    millis = int(round((secs - isecs) * 1000))
    return (isecs, millis) if millis < 1000 else (isecs+1, 0)


_CURRENT_TIME = None       # Seam for mocking time-dependent tests
START_TIME = _get_timetuple()


def timestr_to_secs(timestr):
    """Parses time in format like '1h 10s' and returns time in seconds (float).

    Given time must be in format '1d 2h 3m 4s 5ms' with following rules.
    - Time parts having zero value can be ignored (e.g. '3m 4s' is ok)
    - Format is case and space insensitive
    - Instead of 'd' it is also possible to use 'day' or 'days'
    - Instead of 'h' also 'hour' and 'hours' are ok
    - Instead of 'm' also 'minute', 'minutes', 'min' and 'mins' are ok
    - Instead of 's' also 'second', 'seconds', 'sec' and 'secs' are ok
    - Instead of 'ms' also 'millisecond', 'milliseconds' and 'millis' are ok
    - It is possible to give time only as a float and then it is considered
      to be seconds (e.g. '123', '123.0', '123s', '2min 3s' are all equivelant)
    """
    try:
        secs = _timestr_to_secs(timestr)
    except (ValueError, TypeError):
        raise ValueError("Invalid time string '%s'" % timestr)
    return round(secs, 3)

def _timestr_to_secs(timestr):
    timestr = _normalize_timestr(timestr)
    if timestr == '':
        raise ValueError
    try:
        return float(timestr)
    except ValueError:
        pass
    millis = secs = mins = hours = days = 0
    if timestr[0] == '-':
        sign = -1
        timestr = timestr[1:]
    else:
        sign = 1
    temp = []
    for c in timestr:
        if   c == 'x': millis = float(''.join(temp)); temp = []
        elif c == 's': secs   = float(''.join(temp)); temp = []
        elif c == 'm': mins   = float(''.join(temp)); temp = []
        elif c == 'h': hours  = float(''.join(temp)); temp = []
        elif c == 'p': days   = float(''.join(temp)); temp = []
        else: temp.append(c)
    if temp:
        raise ValueError
    return sign * (millis/1000 + secs + mins*60 + hours*60*60 + days*60*60*24)

def _normalize_timestr(timestr):
    if isinstance(timestr, (int, long, float)):
        return timestr
    timestr = normalize(timestr)
    for item in 'milliseconds', 'millisecond', 'millis':
        timestr = timestr.replace(item, 'ms')
    for item in 'seconds', 'second', 'secs', 'sec':
        timestr = timestr.replace(item, 's')
    for item in 'minutes', 'minute', 'mins', 'min':
        timestr = timestr.replace(item, 'm')
    for item in 'hours', 'hour':
        timestr = timestr.replace(item, 'h')
    for item in 'days', 'day':
        timestr = timestr.replace(item, 'd')
    # 1) 'ms' -> 'x' to ease processing later
    # 2) 'd' -> 'p' because float('1d') returns 1.0 in Jython (bug submitted)
    return timestr.replace('ms','x').replace('d','p')


def secs_to_timestr(secs, compact=False):
    """Converts time in seconds to a string representation.

    Returned string is in format like
    '1 day 2 hours 3 minutes 4 seconds 5 milliseconds' with following rules.
    - Time parts having zero value are not included (e.g. '3 minutes 4 seconds'
    instead of '0 days 0 hours 3 minutes 4 seconds')
    - Hour part has a maximun of 23 and minutes and seconds both have 59
      (e.g. '1 minute 40 seconds' instead of '100 seconds')

    If compact has value 'True', short suffixes are used.
    (e.g. 1d 2h 3min 4s 5ms)
    """
    return _SecsToTimestrHelper(secs, compact).get_value()

class _SecsToTimestrHelper:

    def __init__(self, float_secs, compact):
        self._compact = compact
        self._ret = []
        self._sign, millis, secs, mins, hours, days \
                = self._secs_to_components(float_secs)
        self._add_item(days, 'd', 'day')
        self._add_item(hours, 'h', 'hour')
        self._add_item(mins, 'min', 'minute')
        self._add_item(secs, 's', 'second')
        self._add_item(millis, 'ms', 'millisecond')

    def get_value(self):
        if len(self._ret) > 0:
            return self._sign + ' '.join(self._ret)
        return '0s' if self._compact else '0 seconds'

    def _add_item(self, value, compact_suffix, long_suffix):
        if value == 0:
            return
        if self._compact:
            suffix = compact_suffix
        else:
            suffix = ' %s%s' % (long_suffix, plural_or_not(value))
        self._ret.append('%d%s' % (value, suffix))

    def _secs_to_components(self, float_secs):
        if float_secs < 0:
            sign = '- '
            float_secs = abs(float_secs)
        else:
            sign = ''
        int_secs, millis = _float_secs_to_secs_and_millis(float_secs)
        secs  = int_secs % 60
        mins  = int(int_secs / 60) % 60
        hours = int(int_secs / (60*60)) % 24
        days  = int(int_secs / (60*60*24))
        return sign, millis, secs, mins, hours, days


def format_time(timetuple_or_epochsecs, daysep='', daytimesep=' ', timesep=':',
                millissep=None, gmtsep=None):
    """Returns a timestamp formatted from given time using separators.

    Time can be given either as a timetuple or seconds after epoch.

    Timetuple is (year, month, day, hour, min, sec[, millis]), where parts must
    be integers and millis is required only when millissep is not None.
    Notice that this is not 100% compatible with standard Python timetuples
    which do not have millis.

    Seconds after epoch can be either an integer or a float.
    """
    if isinstance(timetuple_or_epochsecs, (int, long, float)):
        timetuple = _get_timetuple(timetuple_or_epochsecs)
    else:
        timetuple = timetuple_or_epochsecs
    daytimeparts = ['%02d' % t for t in timetuple[:6]]
    day = daysep.join(daytimeparts[:3])
    time_ = timesep.join(daytimeparts[3:6])
    millis = millissep and '%s%03d' % (millissep, timetuple[6]) or ''
    return day + daytimesep + time_ + millis + _diff_to_gmt(gmtsep)

def _diff_to_gmt(sep):
    if not sep:
        return ''
    if time.altzone == 0:
        sign = ''
    elif time.altzone > 0:
        sign = '-'
    else:
        sign = '+'
    minutes = abs(time.altzone) / 60.0
    hours, minutes = divmod(minutes, 60)
    return '%sGMT%s%s%02d:%02d' % (sep, sep, sign, hours, minutes)


def get_time(format='timestamp', time_=None):
    """Return the given or current time in requested format.

    If time is not given, current time is used. How time is returned is
    is deternined based on the given 'format' string as follows. Note that all
    checks are case insensitive.

    - If 'format' contains word 'epoch' the time is returned in seconds after
      the unix epoch.
    - If 'format' contains any of the words 'year', 'month', 'day', 'hour',
      'min' or 'sec' only selected parts are returned. The order of the returned
      parts is always the one in previous sentence and order of words in
      'format' is not significant. Parts are returned as zero padded strings
      (e.g. May -> '05').
    - Otherwise (and by default) the time is returned as a timestamp string in
      format '2006-02-24 15:08:31'
    """
    if time_ is None:
        time_ = time.time()
    format = format.lower()
    # 1) Return time in seconds since epoc
    if 'epoch' in format:
        return int(time_)
    timetuple = time.localtime(time_)
    parts = []
    for i, match in enumerate('year month day hour min sec'.split()):
        if match in format:
            parts.append('%.2d' % timetuple[i])
    # 2) Return time as timestamp
    if not parts:
        return format_time(timetuple, daysep='-')
    # Return requested parts of the time
    elif len(parts) == 1:
        return parts[0]
    else:
        return parts


def parse_time(timestr):
    """Parses the time string and returns its value as seconds since epoch.

    Time can be given in four different formats:

    1) Numbers are interpreted as time since epoch directly. It is possible to
       use also ints and floats, not only strings containing numbers.
    2) Valid timestamp ('YYYY-MM-DD hh:mm:ss' and 'YYYYMMDD hhmmss').
    3) 'NOW' (case-insensitive) is the current time rounded down to the
       closest second.
    4) Format 'NOW - 1 day' or 'NOW + 1 hour 30 min' is the current time
       plus/minus the time specified with the time string.
    """
    try:
        ret = int(timestr)
    except ValueError:
        pass
    else:
        if ret < 0:
            raise ValueError("Epoch time must be positive (got %s)" % timestr)
        return ret
    try:
        return timestamp_to_secs(timestr, (' ', ':', '-', '.'))
    except ValueError:
        pass
    normtime = timestr.lower().replace(' ', '')
    now = int(time.time())
    if normtime == 'now':
        return now
    if normtime.startswith('now'):
        if normtime[3] == '+':
            return now + timestr_to_secs(normtime[4:])
        if normtime[3] == '-':
            return now - timestr_to_secs(normtime[4:])
    raise ValueError("Invalid time format '%s'" % timestr)


def get_timestamp(daysep='', daytimesep=' ', timesep=':', millissep='.'):
    return format_time(_get_timetuple(), daysep, daytimesep, timesep, millissep)


def timestamp_to_secs(timestamp, seps=('', ' ', ':', '.'), millis=False):
    try:
        secs = _timestamp_to_millis(timestamp, seps) / 1000.0
    except (ValueError, OverflowError):
        raise ValueError("Invalid timestamp '%s'" % timestamp)
    if millis:
        return round(secs, 3)
    return int(round(secs))


def secs_to_timestamp(secs, seps=None, millis=False):
    if not seps:
        seps = ('', ' ', ':', '.' if millis else None)
    ttuple = time.localtime(secs)[:6]
    if millis:
        millis = (secs - int(secs)) * 1000
        ttuple = ttuple + (int(millis),)
    return format_time(ttuple, *seps)


def get_start_timestamp(daysep='', daytimesep=' ', timesep=':', millissep=None):
    return format_time(START_TIME, daysep, daytimesep, timesep, millissep)


def get_elapsed_time(start_time, end_time=None, seps=('', ' ', ':', '.')):
    """Returns the time between given timestamps in milliseconds.

    If 'end_time' is not given current timestamp is got with
    get_timestamp using given 'seps'.

    'seps' is a tuple containing 'daysep', 'daytimesep', 'timesep' and
    'millissep' used in given timestamps.
    """
    if start_time == 'N/A' or end_time == 'N/A':
        return 0
    if not end_time:
        end_time = get_timestamp(*seps)
    start_millis = _timestamp_to_millis(start_time, seps)
    end_millis = _timestamp_to_millis(end_time, seps)
    # start/end_millis can be long but we want to return int when possible
    return int(end_millis - start_millis)


def elapsed_time_to_string(elapsed_millis):
    """Converts elapsed time in millisecods to format 'hh:mm:ss.mil'"""
    elapsed_millis = round(elapsed_millis)
    if elapsed_millis < 0:
        pre = '-'
        elapsed_millis = abs(elapsed_millis)
    else:
        pre = ''
    millis = elapsed_millis % 1000
    secs  = int(elapsed_millis / 1000) % 60
    mins  = int(elapsed_millis / 60000) % 60
    hours = int(elapsed_millis / 3600000)
    return '%s%02d:%02d:%02d.%03d' % (pre, hours, mins, secs, millis)


def _timestamp_to_millis(timestamp, seps):
    Y, M, D, h, m, s, millis = _split_timestamp(timestamp, seps)
    secs = time.mktime((Y, M, D, h, m, s, 0, 0, time.daylight))
    return int(round(1000*secs + millis))

def _split_timestamp(timestamp, seps):
    for sep in seps:
        if sep:
            timestamp = timestamp.replace(sep, '')
    timestamp = timestamp.ljust(17, '0')
    years = int(timestamp[:4])
    mons = int(timestamp[4:6])
    days = int(timestamp[6:8])
    hours = int(timestamp[8:10])
    mins = int(timestamp[10:12])
    secs = int(timestamp[12:14])
    millis = int(timestamp[14:17])
    return years, mons, days, hours, mins, secs, millis
