#!/usr/bin/env python
# ----------------------------------------------------------------------------
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
#  Copyright 2008-2015 Nokia Solutions and Networks
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

# Ammended by Timothy Alexander <dragonfyre13@gmail.com>
# (StreamHandler class added)
#   Copyright 2013 Timothy Alexander
#   Licensed under the Apache License, Version 2.0
#      http://www.apache.org/licenses/LICENSE-2.0

#
# Modified by Mateusz Marzec under NSN copyrights
# Copyright 2015 Nokia Solutions and Networks
# * Licensed under the Apache License, Version 2.0,
# * see license.txt file for details.
#

# Ammended by Helio Guilherme <helioxentric@gmail.com>
#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A Robot Framework listener that sends information to a socket

This uses a custom streamhandler module, preferring json but sending either
json or pickle to send objects to the listening server. It should probably be
refactored to call an XMLRPC server.
"""

import copy
import os
import pickle
import platform
import sys
import socket
import threading

PLATFORM = platform.python_implementation()

try:
    import socketserver
except ImportError as e:
    print(f"Exception at TestRunnerAgent import SocketServer: {e}")
    raise e

try:
    # to find robot (we use provided lib)
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../lib'))
    from robot.errors import ExecutionFailed
    from robot.running import EXECUTION_CONTEXTS
    from robot.running.signalhandler import STOP_SIGNAL_MONITOR
    from robot.utils import encoding
    from robot.utils.encoding import SYSTEM_ENCODING
except ImportError:
    encoding = None
    raise

try:
    import json
    _JSONAVAIL = True
except ImportError:
    json = None
    _JSONAVAIL = False

try:
    from StringIO import StringIO
except ImportError:  # py3 <=3.6
    from io import StringIO

HOST = "localhost"

# Setting Output encoding to UTF-8 and ignoring the platform specs
# RIDE will expect UTF-8
# Set output encoding to UTF-8 for piped output streams
# DEBUG This was working in Linux always!
# if encoding:
#     encoding.OUTPUT_ENCODING = 'UTF-8'
#  print("DEBUG: TestRunnerAgent encoding %s\n" % SYSTEM_ENCODING )


class TestRunnerAgent:
    """Pass all listener events to a remote listener

    If called with one argument, that argument is a port
    If called with two, the first is a hostname, the second is a port
    """
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, *args):
        self.port = int(args[0])
        self.host = HOST
        self.sock = None
        self.filehandler = None
        self.streamhandler = None
        self._connect()
        self._send_pid()
        self._create_debugger((len(args) >= 2) and (args[1] == 'True'))
        self._create_kill_server()
        print("TestRunnerAgent: Running under %s %s\n" %
              (PLATFORM, sys.version.split()[0]))

    def _create_debugger(self, pause_on_failure):
        self._debugger = RobotDebugger(pause_on_failure)

    def _create_kill_server(self):
        self._killer = RobotKillerServer(self._debugger)
        self._server_thread = threading.Thread(
            target=self._killer.serve_forever)
        # DEPRECATED: self._server_thread.setDaemon(True)
        self._server_thread.daemon = True
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
        attrs_copy = copy.copy(attrs)
        del attrs_copy['doc']
        attrs_copy['is_dir'] = os.path.isdir(attrs['source'])
        self._send_socket("start_suite", name, attrs_copy)

    def end_suite(self, name, attrs):
        attrs_copy = copy.copy(attrs)
        del attrs_copy['doc']
        attrs_copy['is_dir'] = os.path.isdir(attrs['source'])
        self._send_socket("end_suite", name, attrs_copy)

    def start_keyword(self, name, attrs):
        # pass empty args, see https://github.com/nokia/RED/issues/32

        # we're cutting args from original attrs dict, because it may contain
        # objects which are not json-serializable, and we don't need them anyway
        attrs_copy = copy.copy(attrs)
        del attrs_copy['args']
        del attrs_copy['doc']
        del attrs_copy['assign']

        self._send_socket("start_keyword", name, attrs_copy)
        if self._debugger.is_breakpoint(name, attrs):  # must check original
            self._debugger.pause()
        paused = self._debugger.is_paused()
        if paused:
            self._send_socket('paused')
        self._debugger.start_keyword()
        if paused:
            self._send_socket('continue')

    def end_keyword(self, name, attrs):
        # pass empty args, see https://github.com/nokia/RED/issues/32
        attrs_copy = copy.copy(attrs)
        del attrs_copy['args']
        del attrs_copy['doc']
        del attrs_copy['assign']

        self._send_socket("end_keyword", name, attrs_copy)
        self._debugger.end_keyword(attrs['status'] == 'PASS')

    def message(self, message):
        """ Just ignore it """
        pass

    def log_message(self, message):
        self._send_socket("log_message", message)

    def log_file(self, path):
        self._send_socket("log_file", path)

    def output_file(self, path):
        """ Just ignore it """
        pass

    def report_file(self, path):
        self._send_socket("report_file", path)

    def summary_file(self, path):
        """ Just ignore it """
        pass

    def debug_file(self, path):
        """ Just ignore it """
        pass

    def close(self):
        self._send_socket("close")
        if self.sock:
            self.filehandler.close()
            self.sock.close()

    def _connect(self):
        """Establish a connection for sending data"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            # Iron python does not return right object type if not binary mode
            self.filehandler = self.sock.makefile('wb')
            self.streamhandler = StreamHandler(self.filehandler)
        except socket.error as ex:
            print('unable to open socket to "%s:%s" error: %s'
                  % (self.host, self.port, str(ex)))
            self.sock = None
            self.filehandler = None

    def _send_socket(self, name, *args):
        try:
            if self.filehandler:
                packet = (name, args)
                self.streamhandler.dump(packet)
                self.filehandler.flush()
        except Exception:
            import traceback
            traceback.print_exc(file=sys.stdout)
            sys.stdout.flush()
            raise


class RobotDebugger(object):

    def __init__(self, pause_on_failure=False):
        self._state = 'running'
        self._keyword_level = 0
        self._pause_when_on_level = -1
        self._pause_on_failure = pause_on_failure
        self._resume = threading.Event()

    @staticmethod
    def is_breakpoint(name, attrs):
        if len(attrs['args']) > 0:
            return name == 'BuiltIn.Comment' and \
                   str(attrs['args'][0]).upper().startswith(u"PAUSE")

    def pause(self):
        self._resume.clear()
        self._state = 'pause'

    def pause_on_failure(self, pause):
        self._pause_on_failure = pause

    def resume(self):
        self._state = 'running'
        self._pause_when_on_level = -1
        self._resume.set()

    def step_next(self):
        self._state = 'step_next'
        self._resume.set()

    def step_over(self):
        self._state = 'step_over'
        self._resume.set()

    def start_keyword(self):
        while self._state == 'pause':
            self._resume.wait()
            self._resume.clear()
        if self._state == 'step_next':
            self._state = 'pause'
        elif self._state == 'step_over':
            self._pause_when_on_level = self._keyword_level
            self._state = 'resume'
        self._keyword_level += 1

    def end_keyword(self, passed=True):
        self._keyword_level -= 1
        if self._keyword_level == self._pause_when_on_level or\
                (self._pause_on_failure and not passed):
            self._state = 'pause'

    def is_paused(self):
        return self._state == 'pause'


class RobotKillerServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, debugger):
        socketserver.TCPServer.__init__(self, ("", 0), RobotKillerHandler)
        self.debugger = debugger


class RobotKillerHandler(socketserver.StreamRequestHandler):
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
        elif data == 'step_over':
            self.server.debugger.step_over()
        elif data == 'pause_on_failure':
            self.server.debugger.pause_on_failure(True)
        elif data == 'do_not_pause_on_failure':
            self.server.debugger.pause_on_failure(False)

    @staticmethod
    def _signal_kill():
        try:
            STOP_SIGNAL_MONITOR(1, '')
        except ExecutionFailed:
            pass


# NOTE: Moved to bottom of TestRunnerAgent per feedback in pull request,
#       so jybot doesn't encounter issues. Special imports at top of file.
class StreamError(Exception):
    """
    Base class for EncodeError and DecodeError
    """
    pass


class EncodeError(StreamError):
    """
    This exception is raised when an unencodable object is passed to the
    dump() method or function.
    """
    wrapped_exceptions = (pickle.PicklingError, )


class DecodeError(StreamError):
    """
    This exception is raised when there is a problem decoding an object,
    such as a security violation.

    Note that other exceptions may also be raised during decoding, including
    AttributeError, EOFError, ImportError, and IndexError.
    """
    # NOTE: No JSONDecodeError in json in stdlib for python >= 2.6
    wrapped_exceptions = (pickle.UnpicklingError,)
    if _JSONAVAIL and hasattr(json, 'JSONDecodeError'):
        wrapped_exceptions = (pickle.UnpicklingError, json.JSONDecodeError)


def dump(obj, fp):
    StreamHandler(fp).dump(obj)


def load(fp):
    return StreamHandler(fp).load()


def dumps(obj):
    """
    Similar method to json dumps, prepending data with message length
    header. Replaces 'pickle.dumps', so can be used in place without
    the memory leaks on receiving side in 'pickle.loads' (related to
    memoization of data)

    NOTE: Protocol is ignored when json representation is used
    """
    fp = StringIO()
    StreamHandler(fp).dump(obj)
    return fp.getvalue()


def loads(s):
    """
    Reads in json message or pickle message prepended with message length
    header from a string. Message is expected to be encoded by this class as
    well, to have same message length header type.

    Specifically replaces 'pickle.loads' as that function/method has serious
    memory leak issues with long term use of same Unpickler object for
    encoding data to send, specifically related to memoization of data to
    encode.
    """
    fp = StringIO(s)
    return StreamHandler(fp).load()


class StreamHandler(object):
    """
    This class provides a common streaming approach for the purpose
    of reliably sending data over a socket interface. Replaces usage of
    'Unpickler.load' where possible with JSON format prepended by message length
    header. Uses json in python stdlib (in python >= 2.6) or simplejson (in
    python < 2.6). If neither are available, falls back to pickle.Pickler and
    pickle.Unpickler, attempting to eliminate memory leakage where possible at
    the expense of CPU usage (by not re-using Pickler or Unpickler objects).

    NOTE: StreamHandler currently assumes that same python version is installed
    on both sides of reading/writing (or simplejson is loaded in case of one
    side or other using python < 2.6). This could be resolved by requiring an
    initial header with json vs pickle determination from the writing side, but
    would considerably complicate the protocol(s) further (handshake would need
    to occur at least, and assumes encoding is used over a socket, etc.)

    json.raw_decode could be used rather than prepending with a message header
    in theory (assuming json is available), but performance of repeatedly
    failing to parse written data would make this an unworkable solution in
    many cases.
    """
    loads = staticmethod(loads)
    dumps = staticmethod(dumps)

    def __init__(self, fp):
        """
        Stream handler that encodes objects as either JSON (if available) with
        message length header prepended for sending over a socket, or as a
        pickled object if using python < 2.6 and simplejson is not installed.

        Since 'pickle.load' has memory leak issues with memoization (remembers
        absolutely everything decoded since instantiation), json is a preferred
        method to encode/decode for long-running processes which pass large
        amounts of data back and forth.
        """
        if _JSONAVAIL:
            self._json_encoder = json.JSONEncoder(separators=(',', ':'),
                                                  sort_keys=True).encode
            self._json_decoder = json.JSONDecoder(strict=False).decode
        else:
            def json_not_impl(dummy):
                _ = dummy
                raise NotImplementedError('Python should include json. Please check your Python installation.')
            self._json_decoder = staticmethod(json_not_impl)
            self._json_encoder = staticmethod(json_not_impl)
        self.fp = fp

    def dump(self, obj):
        """
        Similar method to json dump, prepending data with message length
        header. Replaces 'pickle.dump', so can be used in place without
        the memory leaks on receiving side in 'pickle.load' (related to
        memoization of data)

        NOTE: Protocol is ignored when json representation is used
        """
        # NOTE: Slightly less efficient than doing iterencode directly into the
        #       fp, however difference is negligable and reduces complexity of
        #       of the StreamHandler class (treating pickle and json the same)
        write_list = []
        if _JSONAVAIL:
            try:
                s = self._json_encoder(obj)
                write_list.append('J')
                write_list.extend([str(len(s)), '|', s])
            except Exception as ex:
                # Probably just failed to JSON-encode an object; try pickle.
                print(f"Exception at StreamHandler.dump(): {ex}")
        if not write_list:
            s = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
            write_list.append('P')
            write_list.extend([str(len(s)), '|', s])
        self.fp.write(bytes(''.join(write_list), "UTF-8"))

    def load(self):
        """
        Reads in json message prepended with message length header from a file
        (or socket, or other .read() enabled object). Message is expected to be
        encoded by this class as well, to have same message length header type.

        Specifically replaces 'pickle.load' as that function/method has serious
        memory leak issues with long term use of same Unpickler object for
        encoding data to send, specifically related to memoization of data to
        encode.
        """
        header = self._load_header()
        msgtype = header[0]
        msglen = header[1:]
        if not msglen.isdigit():
            raise DecodeError('Message header not valid: %r' % header)
        msglen = int(msglen)
        buff = StringIO()
        # Don't use StringIO.len for sizing, reports string len not bytes
        buff.write(self.fp.read(msglen))
        try:
            if msgtype == 'J':
                return self._json_decoder(buff.getvalue())
            elif msgtype == 'P':
                return pickle.loads(buff.getvalue())
            else:
                raise DecodeError("Message type %r not supported" % msgtype)
        except DecodeError.wrapped_exceptions as ex:
            raise DecodeError(str(ex))

    def _load_header(self):
        """
        Load in just the header bit from a socket/file pointer
        """
        buff = StringIO()
        while len(buff.getvalue()) == 0 or buff.getvalue()[-1] != '|':
            recv_char = self.fp.read(1)
            if not recv_char:
                raise EOFError('File/Socket closed while reading load header')
            buff.write(recv_char)
        return buff.getvalue()[:-1]
