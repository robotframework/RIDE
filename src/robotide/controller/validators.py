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

import os

from robotide.publish.messages import RideInputValidationError

class BaseNameValidator(object):

    def __init__(self, new_basename):
        self._new_basename = new_basename

    def validate(self, context):
        filename = os.path.join(context.directory, '%s.%s' % (self._new_basename, context.get_format()))
        if os.path.exists(filename):
            RideInputValidationError(message="File '%s' already exists" % filename).publish()
            return False
        return True
