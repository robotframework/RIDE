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

from robotide import robotapi
from robotide.spec.iteminfo import LibraryKeywordInfo
from robotide.utils import PY3
if PY3:
    from robotide.utils import unicode


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
    if args.positional:
        parsed.extend(list(args.positional))
    if args.defaults:
        for i, value in enumerate(args.defaults):
            index = len(args.positional) - len(args.defaults) + i
            parsed[index] = parsed[index] + '=' + unicode(value)
    if args.varargs:
        parsed.append('*%s' % args.varargs)
    if args.kwargs:
        parsed.append('**%s' % args.kwargs)
    return parsed
