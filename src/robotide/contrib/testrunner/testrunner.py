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
import SocketServer
import atexit
import codecs
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import signal
import sys
import robotide.utils as utils
from Queue import Empty, Queue
from robot.output.loggerhelper import LEVELS
from robot.utils.encoding import SYSTEM_ENCODING
from robotide.context.platform import IS_WINDOWS
from robotide.contrib.testrunner import TestRunnerAgent
from robotide.controller.testexecutionresults import TestExecutionResults

ATEXIT_LOCK = threading.RLock()

class TestRunner(object):

    def __init__(self, project):
        self._output_dir = None
        self._process = None
        self._server = None
        self._server_thread = None
        self._pause_on_failure = False
        self._pid_to_kill = None
        self._results = TestExecutionResults()
        self.port = None
        self._project = project
        self.profiles = {}

    def enable(self, result_handler):
        self._start_listener_server(result_handler)
        self._create_temporary_directory()

    def _create_temporary_directory(self):
        self._output_dir = tempfile.mkdtemp(".d", "RIDE")
        atexit.register(self._remove_temporary_directory)
        # this plugin creates a temporary directory which _should_
        # get reaped at exit. Sometimes things happen which might
        # cause it to not get deleted. Maybe this would be a good
        # place to check for temporary directories that match the
        # signature and delete them if they are more than a few
        # days old...

    def _remove_temporary_directory(self):
        with ATEXIT_LOCK:
            if os.path.exists(self._output_dir):
                shutil.rmtree(self._output_dir)

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
        self._server_thread.setDaemon(True)
        self._server_thread.start()
        self.port = self._server.server_address[1]

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
        if event == 'end_test':
            longname = args[1]['longname']
            testname = args[0]
            if args[1]['status'] == 'PASS':
                self._results.set_passed(self._get_test_controller(longname,
                                                                   testname))
            else:
                self._results.set_failed(self._get_test_controller(longname,
                                                                   testname))

    def _get_test_controller(self, longname, testname = None):
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

    def set_pause_on_failure(self, pause):
        self._pause_on_failure = pause
        self._send_pause_on_failure_information()

    def _send_pause_on_failure_information(self):
        if self._process:
            self._process.pause_on_failure(self._pause_on_failure)

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

    def get_command(self, profile, pythonpath, monitor_width, names_to_run):
        '''Return the command (as a list) used to run the test'''
        command = profile.get_command_prefix()[:]
        argfile = os.path.join(self._output_dir, "argfile.txt")
        command.extend(["--argumentfile", argfile])
        command.extend(["--listener", self._get_listener_to_cmd()])
        command.append(self._get_suite_source_for_command())
        self._write_argfile(argfile, self._create_standard_args(
            command, profile, pythonpath, monitor_width, names_to_run))
        return command

    @staticmethod
    def get_message_log_level(command):
        min_log_level_number = LEVELS['INFO']
        if '-L' in command:
            switch = '-L'
        elif '--loglevel' in command:
            switch = '--loglevel'
        else:
            return min_log_level_number
        i = command.index(switch)
        if len(command) == i:
            return
        level = command[i+1].upper().split(':')[0]
        return LEVELS.get(level, min_log_level_number)

    def _get_listener_to_cmd(self):
        path = os.path.abspath(TestRunnerAgent.__file__)
        if path[-1] in ['c', 'o']:
            path = path[:-1]
        return '%s:%s:%s' % (path, self.port, self._pause_on_failure)

    def _get_suite_source_for_command(self):
        cur = os.path.abspath(os.path.curdir)
        source = os.path.abspath(self._project.suite.source)
        if not utils.is_same_drive(cur, source):
            return source
        return os.path.abspath(self._project.suite.source)

    def _create_standard_args(
            self, command, profile, pythonpath, monitor_width, names_to_run):
        standard_args = []
        standard_args.extend(profile.get_custom_args())
        self._add_tmp_outputdir_if_not_given_by_user(command, standard_args)
        self._add_pythonpath_if_in_settings_and_not_given_by_user(
            command, standard_args, pythonpath)
        standard_args.extend(["--monitorcolors", "off"])
        standard_args.extend(["--monitorwidth", monitor_width])
        for suite, test in names_to_run:
            standard_args += ['--suite', suite, '--test', test]
        return standard_args

    def _add_tmp_outputdir_if_not_given_by_user(self, command, standard_args):
        if "--outputdir" not in command and "-d" not in command:
            standard_args.extend(["--outputdir", self._output_dir])

    @staticmethod
    def _add_pythonpath_if_in_settings_and_not_given_by_user(
            command, standard_args, pythonpath):
        if '--pythonpath' in command:
            return
        if '-P' in command:
            return
        if not pythonpath:
            return
        standard_args.extend(['--pythonpath', ':'.join(pythonpath)])

    @staticmethod
    def _write_argfile(argfile, args):
        f = codecs.open(argfile, "w", "utf-8")
        f.write("\n".join(args))
        f.close()

    def get_output_and_errors(self, profile):
        stdout, stderr, returncode = self._process.get_output(), \
            self._process.get_errors(), self._process.get_returncode()
        error, log_message = profile.format_error(stderr, returncode)
        return stdout, error, log_message

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
        self._port = None
        self._sock = None
        self._kill_called = False

    def run_command(self, command):
        # We need to supply stdin for subprocess, because otherways in pythonw
        # subprocess will try using sys.stdin which causes an error in windows
        subprocess_args = dict(bufsize=0,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,
                        cwd=self._cwd.encode(SYSTEM_ENCODING))
        if IS_WINDOWS:
            startupinfo = subprocess.STARTUPINFO()
            try:
                import _subprocess
                startupinfo.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
            except ImportError:
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess_args['startupinfo'] = startupinfo
        else:
            subprocess_args['preexec_fn'] = os.setsid
            subprocess_args['shell'] = True
        self._process = subprocess.Popen(command.encode(SYSTEM_ENCODING),
                                         **subprocess_args)
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
        self.resume() # Send so that RF is not blocked
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
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', self._port))
            sock.send(data)
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

    def _kill(self, pid):
        if pid:
            try:
                if os.name == 'nt' and sys.version_info < (2,7):
                    import ctypes
                    ctypes.windll.kernel32.TerminateProcess(
                        int(self._process._handle), -1)
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
        self._thread = threading.Thread(target=self._enqueue_output,
                                        args=(self._stream,))
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
        return result.decode('UTF-8')


# The following two classes implement a small line-buffered socket
# server. It is designed to run in a separate thread, read data
# from the given port and update the UI -- hopefully all in a
# thread-safe manner.
class RideListenerServer(SocketServer.TCPServer):
    """Implements a simple line-buffered socket server"""
    allow_reuse_address = True
    def __init__(self, RequestHandlerClass, callback):
        SocketServer.TCPServer.__init__(self, ("",0), RequestHandlerClass)
        self.callback = callback

class RideListenerHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        decoder = TestRunnerAgent.StreamHandler(self.request.makefile('r'))
        while True:
            try:
                (name, args) = decoder.load()
                self.server.callback(name, *args)
            except (EOFError, IOError):
                # I should log this...
                break
