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
from robot.running import TestLibrary
from robotide.spec.iteminfo import LibraryKeywordInfo


def get_import_result(path, args):
    try:
        lib = TestLibrary(path, args)
        return [
            LibraryKeywordInfo(
                kw.name,
                kw.doc,
                kw.library.name,
                _parse_args(kw.arguments)
            ) for kw in lib.handlers.values()]
    except SystemExit:
        raise ImportError('Library "%s" import failed' % path)

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
