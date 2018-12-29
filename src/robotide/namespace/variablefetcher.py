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
from robotide.utils import PY3
if PY3:
    from robotide.utils import basestring, unicode

# NOTE! This is in own module to reduce the number of dependencies as this is executed in another process

def import_varfile(varfile_path, args):
    temp = robotapi.RobotVariables()
    try:
        temp.set_from_file(varfile_path, args)
    except SystemExit:
        raise robotapi.DataError('Variable file import failed')
    return [(name, _format_value(value), varfile_path)
            for (name, value) in temp.store.data.items()]


# Must be picklable
def _format_value(value):
    if isinstance(value, basestring):
        return value
    if isinstance(value, list):
        return u'[ %s ]' % u' | '.join(unicode(v) for v in value)
    return unicode(value)
