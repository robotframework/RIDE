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
#  Copyright 2010-2012 Nokia Solutions and Networks
#  Copyright 2013-2015 Nokia Networks
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
import signal
import socket
import subprocess
import sys
import threading

from queue import Empty, Queue
from robotide.context import IS_WINDOWS

OUTPUT_ENCODING = sys.getfilesystemencoding()


class Process(object):

    def __init__(self, cwd):
        self._process = None
        self._error_stream = None
        self._output_stream = None
        self._cwd = cwd
        self._port = None
        self._sock = None
        self._kill_called = False

    def run_command(self, command):
        # We need to supply stdin for subprocess, because other ways in python
        # subprocess will try using sys.stdin which causes an error in windows
        # print("DEBUG: enter run_command %s dir %s" % (command, self._cwd))
        subprocess_args = dict(bufsize=0,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               stdin=subprocess.PIPE,
                               cwd=self._cwd)
        if IS_WINDOWS:
            startupinfo = subprocess.STARTUPINFO()
            try:
                import _subprocess
                startupinfo.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
            except ImportError:
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess_args['startupinfo'] = startupinfo
            subprocess_args['env'] = dict(os.environ, PYTHONIOENCODING='UTF-8')
        else:
            subprocess_args['preexec_fn'] = os.setsid
            subprocess_args['shell'] = True
        self._process = subprocess.Popen(command, **subprocess_args)
        self._process.stdin.close()
        self._output_stream = StreamReaderThread(self._process.stdout)
        self._error_stream = StreamReaderThread(self._process.stderr)
        self._output_stream.run()
        self._error_stream.run()
        self._kill_called = False

    def set_port(self, port):
        self._port = port

    def get_output(self):
        return self._output_stream.pop()

    def get_errors(self):
        return self._error_stream.pop()

    def get_returncode(self):
        return self._process.returncode

    def is_alive(self):
        return self._process.poll() is None

    def wait(self):
        self._process.wait()

    def kill(self, force=False, killer_pid=None):
        if not self._process:
            return
        if force:
            self._process.kill()
        self.resume()  # Send so that RF is not blocked
        if IS_WINDOWS and not self._kill_called and self._port is not None:
            self._signal_kill_with_listener_server()
            self._kill_called = True
        else:
            self._kill(killer_pid or self._process.pid)

    def _signal_kill_with_listener_server(self):
        self._send_socket('kill')

    def _send_socket(self, data):
        if self._port is None:
            return  # Silent failure..
        sock = None
        if IS_WINDOWS:
            host = '127.0.0.1'
        else:
            host = 'localhost'
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, self._port))
            sock.send(bytes(data, OUTPUT_ENCODING))
        # except Exception:
        #     print(r"DEBUG: Exception at send socket %s" % data)
        finally:
            sock.close()

    def pause(self):
        self._send_socket('pause')

    def pause_on_failure(self, pause):
        if pause:
            self._send_socket('pause_on_failure')
        else:
            self._send_socket('do_not_pause_on_failure')

    def resume(self):
        self._send_socket('resume')

    def step_next(self):
        self._send_socket('step_next')

    def step_over(self):
        self._send_socket('step_over')

    @staticmethod
    def _kill(pid):
        if pid:
            try:
                os.kill(pid, signal.SIGINT)
            except OSError:
                pass


class StreamReaderThread(object):

    def __init__(self, stream):
        self._queue = Queue()
        self._thread = None
        self._stream = stream

    def run(self):
        self._thread = threading.Thread(target=self._enqueue_output,
                                        args=(self._stream,))
        self._thread.daemon = True
        self._thread.start()

    def _enqueue_output(self, out):
        for line in iter(out.readline, b''):
            self._queue.put(line)

    def pop(self):
        result = b''
        my_queue_rng = range(self._queue.qsize())
        for _ in my_queue_rng:
            try:
                result += self._queue.get_nowait()
            except Empty:
                pass
        return result
