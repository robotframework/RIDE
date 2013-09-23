#!/usr/bin/env python
# Copyright 2013 Timothy Alexander
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

'''streamHandler.py

This module provides a common streaming module (StreamHandler) for the purpose
of reliably sending data over a socket interface. Replaces usage of
Unpickler.load where possible with JSON format prepended by message length
header. Uses json in python stdlib (in python >= 2.6) or simplejson (in python
< 2.6). If neither are available, falls back to pickle.Pickler and
pickle.Unpickler, attempting to eliminate memory leakage where possible at the
expense of CPU usage (by not re-using Pickler or Unpickler objects).

NOTE: StreamHandler currently assumes that same python version is installed on
both sides of reading/writing (or simplejson is loaded in case of one side or
other using python < 2.6). This could be resolved by requiring an initial
header with json vs pickle determination from the writing side, but would
considerably complicate the protocol(s) further (handshake would need to occur
at least, and assumes encoding is used over a socket, etc.)

json.raw_decode could be used rather than prepending with a message header in
theory (assuming json is available), but performance of repeatedly failing
to parse written data would make this an unworkable solution in many cases.
'''

import sys
import socket

if sys.hexversion > 0x2060000:
    import json
    _JSONAVAIL=True
else:
    try:
        import simplejson as json
        _JSONAVAIL=True
    except ImportError:
        _JSONAVAIL=False

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

__all__ = ["StreamError", "DecodeError", "EncodeError", "StreamHandler",
           "dump", "dumps", "load", "loads"]


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
    _wrapped_exceptions = (pickle.PicklingError, )


class DecodeError(StreamError):
    """
    This exception is raised when there is a problem decoding an object,
    such as a security violation.

    Note that other exceptions may also be raised during decoding, including
    AttributeError, EOFError, ImportError, and IndexError.
    """
    # NOTE: No JSONDecodeError in json in stdlib for python >= 2.6
    _wrapped_exceptions = (pickle.UnpicklingError, )

class _Finished(Exception):
    def __init__(self, val):
        self.val = val

def dump(obj, sock):
    StreamHandler(sock).dump(obj)

def load(sock):
    return StreamHandler(sock).load()

def dumps(obj):
    """
    Similar method to json dumps, prepending data with message length
    header. Replaces pickle.dumps, so can be used in place without
    the memory leaks on receiving side in pickle.loads (related to
    memoization of data)
    
    NOTE: Protocol is ignored when json representation is used
    """
    fp = StringIO()
    StreamHandler(fp).dump(obj)
    return fp.getvalue()

def loads(str):
    """
    Reads in json message or pickle message prepended with message length
    header from a string. Message is expected to be encoded by this class as
    well, to have same message length header type.
    
    Specifically replaces pickle.loads as that function/method has serious
    memory leak issues with long term use of same Unpickler object for
    encoding data to send, specifically related to memoization of data to
    encode.
    """
    fp = StringIO(s)
    return StreamHandler(fp).load()


class StreamHandler(object):
    loads = staticmethod(loads)
    dumps = staticmethod(dumps)
    
    def __init__(self, sock):
        """
        Stream handler that encodes objects as either JSON (if available) with
        message length header prepended for sending over a socket, or as a
        pickled object if using python < 2.6 and simplejson is not installed.
        
        Since pickle.load has memory leak issues with memoization (remembers
        absolutely everything decoded since instantiation), json is a preferred
        method to encode/decode for long running processes which pass large
        amounts of data back and forth.
        """
        if JSONAVAIL:
            self._json_encoder = json.JSONEncoder(separators=(',', ':'),
                                        sort_keys=True).encode
            self._json_decoder = json.JSONDecoder(strict=False).decode
        else:
            def json_not_impl(obj):
                raise NotImplementedError(
                    'Python version < 2.6 and simplejson not installed. Please'
                    ' install simplejson.')
            self._json_decoder = staticmethod(json_not_impl)
            self._json_encoder = staticmethod(json_not_impl)
        self.sock = sock

    def dump(self, obj):
        """
        Similar method to json dump, prepending data with message length
        header. Replaces pickle.dump, so can be used in place without
        the memory leaks on receiving side in pickle.load (related to
        memoization of data)
        
        Note, class takes a socket rather than a file, as this is the intended
        communication method.
        
        NOTE: Protocol is ignored when json representation is used
        """
        # NOTE: Slightly less efficient than doing iterencode directly into the
        #       fp, however difference is negligable and reduces complexity of
        #       of the StreamHandler class (treating pickle and json the same)
        write_list = []
        if _JSONAVAIL:
            write_list.append('J')
            s = self._json_encoder(obj)
            write_list.extend([str(sys.getsizeof(s)), '|', s])
        else:
            write_list.append('P')
            try:
                s = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
            except EncodeError._wrapped_exceptions, e:
                raise EncodeError(str(e))
            write_list.extend([str(sys.getsizeof(s)), '|', s])
        try:
            sock.sendall(''.join(write_list))
        except socket.error, e:
            # python <2.6 does not make socket.error a subclass of IOError
            raise IOError(str(e))

    def load():
        """
        Reads in json message prepended with message length header from a file
        (or socket, or other .read() enabled object). Message is expected to be
        encoded by this class as well, to have same message length header type.
        
        Specifically replaces pickle.load as that function/method has serious
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
        bytes_left = msglen
        buff = StringIO()
        # Don't use StringIO.len for sizing, reports string len not bytes
        while bytes_left:
            try:
                s = self.sock.recv(bytes_left)
            except socket.error, e:
                # python <2.6 does not make socket.error a subclass of IOError
                raise IOError(str(e))
            if not s:
                raise EOFError
            buff.write(s)
            bytes_left = msglen - sys.getsizeof(buff.getvalue())
        try:
            if msgtype == 'J':
                return self._json_decoder(buff.getvalue())
            elif msgtype == 'P':
                return pickle.load(buff)
            else:
                raise DecodeError("Message type %r not supported" % msgtype)
        except DecodeError._wrapped_exceptions, e:
            raise DecodeError(str(e))
        
    def _load_header():
        """
        Load in just the header bit from a socket
        """
        buff = StringIO()
        while buff.getvalue()[-1] != '|':
            try:
                s = self.sock.recv(1)
            except socket.error, e:
                # python <2.6 does not make socket.error a subclass of IOError
                raise IOError(str(e))
            if not s:
                raise EOFError
            buff.write(s)
        return buff.getvalue()[:-1]
