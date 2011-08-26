#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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

class LocalNamespace(object):

    def __init__(self, controller, namespace, row=None):
        self._controller = controller
        self._namespace = namespace
        self._row = row

    def has_name(self, value):
        if self._row:
            for row, step in enumerate(self._controller.steps):
                if self._row == row:
                    break
                for assignment in step._step.assign:
                    if assignment.replace('=', '').strip() == value:
                        return True
        for sug in self._namespace.get_suggestions_for(self._controller, value):
            if sug.name == value:
                return True
        return False
