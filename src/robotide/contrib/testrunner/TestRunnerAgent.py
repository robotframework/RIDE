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

# Modified by Mikko Korpela under NSN copyrights
#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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

'''A Robot Framework listener that sends information to a socket

This uses the "pickle" module of python to send objects to the
listening server. It should probably be refactored to call an
XMLRPC server.
'''

import os
import socket
import threading
import SocketServer
import time

try:
    # RF 2.7.5
    from robot.running import EXECUTION_CONTEXTS
    def _is_logged(level):
        current = EXECUTION_CONTEXTS.current
        if current is None:
            return True
        out = current.output
        if out is None:
            return True
        return out._xmllogger._log_message_is_logged(level)
except ImportError:
    # RF 2.5.6
    # RF 2.6.3
    def _is_logged(level):
        from robot.output import OUTPUT # Needs to be imported in the function as OUTPUT is not a constant
        if OUTPUT is None:
            return True
        return OUTPUT._xmllogger._log_message_is_logged(level)

from robot.running.signalhandler import STOP_SIGNAL_MONITOR
from robot.errors import ExecutionFailed


try:
    import cPickle as pickle
except ImportError:
    import pickle

PORT = 5007
HOST = "localhost"


# Setting Output encoding to UTF-8 and ignoring the platform specs
# RIDE will expect UTF-8
import robot.utils.encoding
robot.utils.encoding.OUTPUT_ENCODING = 'UTF-8' # Set output encoding to UTF-8 for piped output streams
robot.utils.encoding._output_encoding = robot.utils.encoding.OUTPUT_ENCODING # RF 2.6.3 and RF 2.5.7

class TestRunnerAgent:
    """Pass all listener events to a remote listener

    If called with one argument, that argument is a port
    If called with two, the first is a hostname, the second is a port
    """
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, *args):
        self.port = PORT
        self.host = HOST
        self.sock = None
        if len(args) == 1:
            self.port = int(args[0])
        elif len(args) >= 2:
            self.host = args[0]
            self.port = int(args[1])
        self._connect()
        self._send_pid()
        self._create_debugger()
        self._create_kill_server()

    def _create_debugger(self):
        self._debugger = RobotDebugger()

    def _create_kill_server(self):
        self._killer = RobotKillerServer(self._debugger)
        self._server_thread = threading.Thread(target=self._killer.serve_forever)
        self._server_thread.setDaemon(True)
        self._server_thread.start()
        self._send_server_port(self._killer.server_address[1])

    def _send_pid(self):
        self._send_socket("pid", os.getpid())

    def _send_server_port(self, port):
        self._send_socket("port", port)

    def start_test(self, name, attrs):
        self._send_socket("start_test", name, attrs)

    def end_test(self, name, attrs):
        self._send_socket("end_test", name, attrs)

    def start_suite(self, name, attrs):
        self._send_socket("start_suite", name, attrs)

    def end_suite(self, name, attrs):
        self._send_socket("end_suite", name, attrs)

    def start_keyword(self, name, attrs):
        self._send_socket("start_keyword", name, attrs)
        self._debugger.start_keyword()

    def end_keyword(self, name, attrs):
        self._send_socket("end_keyword", name, attrs)
        self._debugger.end_keyword()

    def message(self, message):
        pass

    def log_message(self, message):
        if _is_logged(message['level']):
            self._send_socket("log_message", message)

    def log_file(self, path):
        self._send_socket("log_file", path)

    def output_file(self, path):
        pass

    def report_file(self, path):
        self._send_socket("report_file", path)

    def summary_file(self, path):
        pass

    def debug_file(self, path):
        pass

    def close(self):
        self._send_socket("close")
        if self.sock:
            self.filehandler.close()
            self.sock.close()

    def _connect(self):
        '''Establish a connection for sending pickles'''
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            # Iron python does not return right kind of objects if binary mode is not used
            self.filehandler = self.sock.makefile('wb')
            self.pickler = pickle.Pickler(self.filehandler)
        except socket.error, e:
            print 'unable to open socket to "%s:%s" error: %s' % (self.host, self.port, str(e))
            self.sock = None

    def _send_socket(self, name, *args):
        if self.sock:
            packet = (name, args)
            self.pickler.dump(packet)
            self.filehandler.flush()


class RobotDebugger(object):

    def __init__(self):
        self.pause_lock = threading.RLock()
        self.stepper_lock = threading.RLock()

    def pause(self):
        self.pause_lock.acquire()

    def resume(self):
        self.pause_lock.release()

    def step_next(self):
        self.pause_lock.release()
        with self.stepper_lock:
            self.pause_lock.acquire()

    def start_keyword(self):
        with self.stepper_lock:
            with self.pause_lock:
                pass

    def end_keyword(self):
        pass



class RobotKillerServer(SocketServer.TCPServer):
    allow_reuse_address = True
    def __init__(self, debugger):
        SocketServer.TCPServer.__init__(self, ("",0), RobotKillerHandler)
        self.debugger = debugger

class RobotKillerHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        data = self.request.makefile('r').read().strip()
        if data == 'kill':
            self._signal_kill()
        elif data == 'pause':
            self.server.debugger.pause()
        elif data == 'resume':
            self.server.debugger.resume()
        elif data == 'step_next':
            self.server.debugger.step_next()

    def _signal_kill(self):
        try:
            STOP_SIGNAL_MONITOR(1,'')
        except ExecutionFailed:
            pass
