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
from Queue import Empty
from multiprocessing import Queue
from multiprocessing.process import Process
import sys
from robot.running import TestLibrary
from robotide.spec.iteminfo import LibraryKeywordInfo

def import_library(path, args):
    q = Queue(maxsize=1)
    p = Process(target=_library_initializer, args=(q, path, args))
    p.start()
    while True:
        try:
            result = q.get(timeout=0.1)
            if isinstance(result, Exception):
                raise ImportError(result)
            return result
        except Empty:
            if not p.is_alive():
                raise ImportError()

def _library_initializer(queue, path, args):
    try:
        queue.put(_get_keywords(path, args))
    except Exception, e:
        queue.put(e)
    finally:
        sys.exit()

def _get_keywords(path, args):
    lib = TestLibrary(path, args)
    return [
        LibraryKeywordInfo(
            kw.name,
            kw.doc,
            kw.library.name,
            _parse_args(kw.arguments)
        ) for kw in lib.handlers.values()]

def _parse_args(handler_args):
    args = []
    if handler_args.names:
        args.extend(list(handler_args.names))
    if handler_args.defaults:
        for i, value in enumerate(handler_args.defaults):
            index = len(handler_args.names) - len(handler_args.defaults) + i
            args[index] = args[index] + '=' + unicode(value)
    if handler_args.varargs:
        args.append('*%s' % handler_args.varargs)
    return args
