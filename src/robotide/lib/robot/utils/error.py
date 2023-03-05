#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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

import os
import sys
import traceback

from robotide.lib.robot.errors import RobotError

from .platform import RERAISED_EXCEPTIONS
from .unic import unic


EXCLUDE_ROBOT_TRACES = not os.getenv('ROBOT_INTERNAL_TRACES')

Throwable = ()


def get_error_message():
    """Returns error message of the last occurred exception.

    This method handles also exceptions containing unicode messages. Thus, it
    MUST be used to get messages from all exceptions originating outside the
    framework.
    """
    return ErrorDetails().message


def get_error_details(exclude_robot_traces=EXCLUDE_ROBOT_TRACES):
    """Returns error message and details of the last occurred exception."""
    details = ErrorDetails(exclude_robot_traces=exclude_robot_traces)
    return details.message, details.traceback


def ErrorDetails(exc_info=None, exclude_robot_traces=EXCLUDE_ROBOT_TRACES):
    """This factory returns an object that wraps the last occurred exception

    It has attributes `message`, `traceback` and `error`, where `message`
    contains type and message of the original error, `traceback` contains the
    traceback/stack trace and `error` contains the original error instance.
    """
    exc_type, exc_value, exc_traceback = exc_info or sys.exc_info()
    if exc_type in RERAISED_EXCEPTIONS:
        raise exc_value
    return PythonErrorDetails(exc_type, exc_value, exc_traceback, exclude_robot_traces)


class _ErrorDetails(object):
    _generic_exception_names = ('AssertionError', 'AssertionFailedError',
                                'Exception', 'Error', 'RuntimeError',
                                'RuntimeException')

    def __init__(self, exc_type, exc_value, exc_traceback,
                 exclude_robot_traces=True):
        self.error = exc_value
        self._exc_type = exc_type
        self._exc_traceback = exc_traceback
        self._exclude_robot_traces = exclude_robot_traces
        self._message = None
        self._traceback = None

    @property
    def message(self):
        if self._message is None:
            self._message = self._get_message()
        return self._message

    def _get_message(self):
        raise NotImplementedError

    @property
    def traceback(self):
        if self._traceback is None:
            self._traceback = self._get_details()
        return self._traceback

    def _get_details(self):
        raise NotImplementedError

    @staticmethod
    def _get_name(exc_type):
        try:
            return exc_type.__name__
        except AttributeError:
            return unic(exc_type)

    def _format_message(self, name, message):
        message = unic(message or '')
        message = self._clean_up_message(message, name)
        name = name.split('.')[-1]  # Use only last part of the name
        if not message:
            return name
        if self._is_generic_exception(name):
            return message
        return '%s: %s' % (name, message)

    def _is_generic_exception(self, name):
        return (name in self._generic_exception_names or
                isinstance(self.error, RobotError) or
                getattr(self.error, 'ROBOT_SUPPRESS_NAME', False))

    @staticmethod
    def _clean_up_message(message, name=None):
        _ = name
        return message


class PythonErrorDetails(_ErrorDetails):

    def _get_message(self):
        name = self._get_name(self._exc_type)
        return self._format_message(name, unic(self.error))

    def _get_details(self):
        if isinstance(self.error, RobotError):
            return self.error.details
        return 'Traceback (most recent call last):\n' + self._get_traceback()

    def _get_traceback(self):
        tb = self._exc_traceback
        while tb and self._is_excluded_traceback(tb):
            tb = tb.tb_next
        return ''.join(traceback.format_tb(tb)).rstrip() or '  None'

    def _is_excluded_traceback(self, ltraceback):
        if not self._exclude_robot_traces:
            return False
        module = ltraceback.tb_frame.f_globals.get('__name__')
        return module and module.startswith('robot.')
