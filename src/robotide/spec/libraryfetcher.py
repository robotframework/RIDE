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

from .. import robotapi
from .iteminfo import LibraryKeywordInfo


def get_import_result(path, args):
    lib = robotapi.TestLibrary(path, args)
    kws = [
        LibraryKeywordInfo(
            kw.name,
            kw.doc,
            lib.doc_format,
            kw.library.name,
            _parse_args(kw.arguments)
        ) for kw in lib.handlers]
    return kws


def _parse_args(args):
    parsed = []
    for name in args.positional:
        parsed.append('='.join([name, str(args.defaults[name])]) if name in args.defaults else name)
    if args.varargs:
        parsed.append('*%s' % args.varargs)
    for name in args.kwonlyargs:
        parsed.append('='.join([name, str(args.defaults[name])]) if name in args.defaults else name)
    if args.kwargs:
        parsed.append('**%s' % args.kwargs)
    return parsed
