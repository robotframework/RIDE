import time


class TimestampGenerator(object):

    def __init__(self):
        self._previous_secs = None
        self._previous_separators = None
        self._previous_timestamp = None

    def get_timestamp(self, daysep='', daytimesep=' ', timesep=':', millissep='.'):
        epoch = self._get_epoch()
        secs, millis = _float_secs_to_secs_and_millis(epoch)
        if self._use_cache(secs, daysep, daytimesep, timesep):
            return self._cached_timestamp(millis, millissep)
        timestamp = format_time(epoch, daysep, daytimesep, timesep, millissep)
        self._cache_timestamp(secs, timestamp, daysep, daytimesep, timesep, millissep)
        return timestamp

    # Seam for mocking
    def _get_epoch(self):
        return time.time()

    def _use_cache(self, secs, *separators):
        return self._previous_timestamp \
            and self._previous_secs == secs \
            and self._previous_separators == separators

    def _cached_timestamp(self, millis, millissep):
        if millissep:
            return '%s%s%03d' % (self._previous_timestamp, millissep, millis)
        return self._previous_timestamp

    def _cache_timestamp(self, secs, timestamp, daysep, daytimesep, timesep, millissep):
        self._previous_secs = secs
        self._previous_separators = (daysep, daytimesep, timesep)
        self._previous_timestamp = timestamp[:-4] if millissep else timestamp


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


def _float_secs_to_secs_and_millis(secs):
    isecs = int(secs)
    millis = int(round((secs - isecs) * 1000))
    return (isecs, millis) if millis < 1000 else (isecs+1, 0)

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

def _get_timetuple(epoch_secs=None):
    if epoch_secs is None:  # can also be 0 (at least in unit tests)
        epoch_secs = time.time()
    secs, millis = _float_secs_to_secs_and_millis(epoch_secs)
    timetuple = time.localtime(secs)[:6]  # from year to secs
    return timetuple + (millis,)

START_TIMESTAMP = _get_timetuple()
def get_start_timestamp(self, daysep='', daytimesep=' ', timesep=':', millissep=None):
    return format_time(START_TIMESTAMP, daysep, daytimesep, timesep, millissep)
