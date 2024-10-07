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
import subprocess
import tempfile
import time
from ..publish import RideRunnerStarted, RideRunnerStopped


class Process(object):

    def __init__(self, command):
        self._command = self._parse_command(command)
        self._process = None
        self._error = None
        self._out_file = None
        self._out_path = None
        self._out_fd = None
        self._fuse = False
        self._pid =None

    @property
    def pid(self):
        return self._pid

    @staticmethod
    def _parse_command(command):
        if isinstance(command, str):
            return [val.replace('<SPACE>', ' ') for val in command.split()]
        return command

    def start(self):
        self._out_fd, self._out_path = tempfile.mkstemp(prefix='rfproc_', suffix='.txt', text=True)
        self._out_file = open(self._out_path, 'w+b')
        if not self._command:
            self._error = 'The command is missing from this run configuration.'
            return
        try:
            self._process = subprocess.Popen(self._command, stdout=self._out_fd, stderr=subprocess.STDOUT)
            self._pid = self._process.pid
            RideRunnerStarted(process=self._pid).publish()
        except OSError as err:
            self._error = str(err)

    def is_finished(self):
        return self._error is not None or self._process.poll() is not None

    def stop(self):
        self._process.kill()
        self._close_outputs()
        RideRunnerStopped(process=self._pid).publish()

    def wait(self):
        if self._process is not None:
            self._process.wait()

    def get_output(self, wait_until_finished=False):
        """Returns the output produced by the process.

        If ``wait_until_finished`` is True, blocks until the process is
        finished and returns all output. Otherwise, the currently available
        output is returned immediately.

        Currently available output depends on buffering and might not include
        everything that has been written by the process.
        """
        if self._error:
            self._close_outputs()
            return self._error
        if wait_until_finished:
            self._process.wait()
        try:
            output = self._out_file.read()
        except ValueError:
            output = b"\nRIDE: ValueError when reading output.\n\n"
            self._fuse = True
            self._close_outputs()
            return output
        if self.is_finished():
            self._close_outputs()
        return output

    def _close_outputs(self):
        self._out_file.close()
        try:
            if not self._fuse:
                os.close(self._out_fd)
            self._remove_tempfile()
        except ValueError:
            self._fuse = True
            return

    def _remove_tempfile(self, attempts=5):
        try:
            os.remove(self._out_path)
        except OSError:
            if not attempts:
                self._fuse = True
                return
            time.sleep(1)
            self._remove_tempfile(attempts - 1)
