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

import socketserver as SocketServer
import threading

from robotide.contrib.testrunner.Process import Process
from robotide.contrib.testrunner.TestRunnerAgent import StreamHandler
from robotide.controller.testexecutionresults import TestExecutionResults


# Solution from https://stackoverflow.com/questions/10009753/
# python-dealing-with-mixed-encoding-files
def mixed_decoder(unicode_error):
    err_str = unicode_error[1]
    err_len = unicode_error.end - unicode_error.start
    next_position = unicode_error.start + err_len
    err_hex = err_str[unicode_error.start:unicode_error.end].encode('hex')
    # Alternative, return u'?', next_position
    return u'%s' % err_hex, next_position  # Comment this line out to get a ?

# codecs.register_error("mixed", mixed_decoder)


class TestRunner(object):

    def __init__(self, project):
        self._process = None
        self._server = None
        self._server_thread = None
        self._pause_on_failure = False
        self._pid_to_kill = None
        self._results = TestExecutionResults()
        self._port = None
        self._project = project
        self.profiles = {}
        self._pause_longname = None
        self._pause_testname = None

    def enable(self, result_handler):
        self._start_listener_server(result_handler)

    def add_profile(self, name, item):
        self.profiles[name] = item

    def get_profile(self, name):
        return self.profiles[name]

    def get_profile_names(self):
        return sorted(self.profiles.keys())

    def _start_listener_server(self, result_handler):
        def handle(*args):
            self._result_handler(*args)
            result_handler(*args)

        self._server = RideListenerServer(RideListenerHandler, handle)
        self._server_thread = threading.Thread(
            target=self._server.serve_forever)
        # DEPRECATED: self._server_thread.setDaemon(True)
        self._server_thread.daemon = True
        self._server_thread.start()
        self._port = self._server.server_address[1]

    def _result_handler(self, event, *args):
        if event == 'pid':
            self._pid_to_kill = int(args[0])
        if event == 'port' and self._process:
            self._process.set_port(args[0])
        if event == 'start_test':
            longname = args[1]['longname']
            testname = args[0]
            self._results.set_running(self._get_test_controller(longname,
                                                                testname))
            self._pause_longname = longname
            self._pause_testname = testname

        if event == 'continue':
            self._results.set_running(self._get_test_controller(
                self._pause_longname, self._pause_testname))

        if event == 'paused':
            self._results.set_paused(self._get_test_controller(
                self._pause_longname, self._pause_testname))
        if event == 'end_test':
            longname = args[1]['longname']
            testname = args[0]
            if args[1]['status'] == 'PASS':
                self._results.set_passed(self._get_test_controller(longname,
                                                                   testname))
            elif args[1]['status'] == 'SKIP':
                self._results.set_skipped(self._get_test_controller(longname,
                                                                    testname))
            else:
                self._results.set_failed(self._get_test_controller(longname,
                                                                   testname))

    def _get_test_controller(self, longname, testname=None):
        ret = self._project.find_controller_by_longname(longname, testname)
        return ret

    def clear_server(self):
        self._server = None

    def shutdown_server(self):
        if self._server:
            self._server.shutdown()

    def test_execution_started(self):
        self._results.test_execution_started()

    def kill_process(self):
        if self._process:
            self._process.kill(force=True)

    def send_pause_on_failure(self, pause):
        if self._process:
            self._process.pause_on_failure(pause)

    def send_stop_signal(self):
        if self._process:
            self._process.kill(killer_pid=self._pid_to_kill)

    def send_pause_signal(self):
        if self._process:
            self._process.pause()

    def send_continue_signal(self):
        if self._process:
            self._process.resume()

    def send_step_next_signal(self):
        if self._process:
            self._process.step_next()

    def send_step_over_signal(self):
        if self._process:
            self._process.step_over()

    def run_command(self, command, cwd):
        self._pid_to_kill = None
        self._process = Process(cwd)
        self._process.run_command(command)

    def get_output_and_errors(self, profile):
        stdout, stderr, returncode = self._process.get_output(), \
                                     self._process.get_errors(), \
                                     self._process.get_returncode()
        error, log_message = profile.format_error(stderr, returncode)
        return stdout, error, log_message

    def get_listener_port(self):
        return self._port

    def is_running(self):
        return self._process and self._process.is_alive()

    def command_ended(self):
        self._results.set_stopped(None)
        self._process = None


# The following two classes implement a small line-buffered socket
# server. It is designed to run in a separate thread, read data
# from the given port and update the UI -- hopefully all in a
# thread-safe manner.
class RideListenerServer(SocketServer.TCPServer):
    """Implements a simple line-buffered socket server"""
    allow_reuse_address = True

    def __init__(self, request_handler_class, callback):
        SocketServer.TCPServer.__init__(self, ("", 0), request_handler_class)
        self.callback = callback


class RideListenerHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        decoder = StreamHandler(self.request.makefile('r'))
        while True:
            try:
                (name, args) = decoder.load()
                self.server.callback(name, *args)
            except (EOFError, IOError):
                # I should log this...
                break
