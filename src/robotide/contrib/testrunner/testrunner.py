# Copyright 2010 Orbitz WorldWide
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Modified by NSN
#  Copyright 2010-2012 Nokia Siemens Networks Oyj
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
from Queue import Empty, Queue
import os
import socket
import subprocess
import threading
import signal
import sys
from robot.utils.encoding import SYSTEM_ENCODING
from robot.utils.encodingsniffer import DEFAULT_OUTPUT_ENCODING
from robotide.context.platform import IS_WINDOWS
from robotide.controller.testexecutionresults import TestExecutionResults


class TestRunner(object):

    def __init__(self):
        self._process = None
        self._results = TestExecutionResults()

    def set_running(self, test):
        self._results.set_running(test)

    def set_passed(self, test):
        self._results.set_passed(test)

    def set_failed(self, test):
        self._results.set_failed(test)

    def test_execution_started(self):
        self._results.test_execution_started()

    def kill_process(self):
        if self._process:
            self._process.kill(force=True)

    def send_stop_signal(self):
        if self._process:
            self._process.kill(killer_pid=self._pid_to_kill, killer_port=self._killer_port)

    def run_command(self, command, cwd):
        self._pid_to_kill = None
        self._killer_port = None
        self._process = Process(cwd)
        self._process.run_command(command)

    def set_pid_to_kill(self, pid):
        self._pid_to_kill = pid

    def set_killer_port(self, port):
        self._killer_port = port

    def get_output_and_errors(self):
        return self._process.get_output(), self._process.get_errors()

    def is_running(self):
        return self._process and self._process.is_alive()

    def command_ended(self):
        self._process = None


class Process(object):

    def __init__(self, cwd):
        self._process = None
        self._error_stream = None
        self._output_stream = None
        self._cwd = cwd

    def run_command(self, command):
        # We need to supply an stdin for subprocess, because otherways in pythonw
        # subprocess will try using sys.stdin which will cause an error in windows
        self._process = subprocess.Popen(
            command.encode(SYSTEM_ENCODING),
            bufsize=0,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            shell=False if IS_WINDOWS else True,
            cwd=self._cwd.encode(SYSTEM_ENCODING),
            preexec_fn=os.setsid if not IS_WINDOWS else None)
        self._process.stdin.close()
        self._output_stream = StreamReaderThread(self._process.stdout)
        self._error_stream = StreamReaderThread(self._process.stderr)
        self._output_stream.run()
        self._error_stream.run()
        self._kill_called = False

    def get_output(self):
        return self._output_stream.pop()

    def get_errors(self):
        return self._error_stream.pop()

    def is_alive(self):
        return self._process.poll() is None

    def wait(self):
        self._process.wait()

    def kill(self, force=False, killer_port=None, killer_pid=None):
        if not self._process:
            return
        if force:
            self._process.kill()
        if IS_WINDOWS and not self._kill_called and killer_port:
            self._signal_kill_with_listener_server(killer_port)
            self._kill_called = True
        else:
            self._kill(killer_pid or self._process.pid)

    def _signal_kill_with_listener_server(self, killer_port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', killer_port))
        sock.send('kill\n')
        sock.close()

    def _kill(self, pid):
        if pid:
            try:
                if os.name == 'nt' and sys.version_info < (2,7):
                    import ctypes
                    ctypes.windll.kernel32.TerminateProcess(int(self._process._handle), -1)
                else:
                    os.kill(pid, signal.SIGINT)
            except OSError:
                pass


class StreamReaderThread(object):

    def __init__(self, stream):
        self._queue = Queue()
        self._thread = None
        self._stream = stream

    def run(self):
        self._thread = threading.Thread(target=self._enqueue_output, args=(self._stream,))
        self._thread.daemon = True
        self._thread.start()

    def _enqueue_output(self, out):
        for line in iter(out.readline, b''):
            self._queue.put(line)

    def pop(self):
        result = ""
        for _ in xrange(self._queue.qsize()):
            try:
                result += self._queue.get_nowait()
            except Empty:
                pass
        return result.decode(DEFAULT_OUTPUT_ENCODING)
