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
from robot.variables import Variables as RobotVariables
from robot.errors import DataError

# NOTE! This is in own module to reduce the number of dependencies as this is executed in another process

def import_varfile_in_another_process(varfile_path, args):
    q = Queue()
    p = Process(target=set_from_file, args=(q, varfile_path, args))
    p.start()
    p.join()
    while True:
        try:
            results = q.get(timeout=0.1)
            if isinstance(results, DataError):
                raise DataError(results)
            return results
        except Empty:
            if not p.is_alive():
                raise DataError('No variables')


def set_from_file(queue, varfile_path, args):
    queue.put(_get_vars(varfile_path, args))

def _get_vars(varfile_path, args):
    try:
        temp = RobotVariables()
        temp.set_from_file(varfile_path, args)
        return [(name, _format_value(value), varfile_path) for (name, value) in temp.items()]
    except DataError, e:
        return e

# Must be pickable
def _format_value(value):
    if isinstance(value, basestring):
        return value
    if isinstance(value, list):
        return u'[ %s ]' % u' | '.join(unicode(v) for v in value)
    return unicode(value)
