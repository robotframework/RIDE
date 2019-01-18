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

from robotide import utils
from robotide.spec.iteminfo import LocalVariableInfo


def LocalNamespace(controller, namespace, row=None):
    if row is not None: # can be 0!
        return LocalRowNamespace(controller, namespace, row)
    return LocalMacroNamespace(controller, namespace)


class LocalMacroNamespace(object):

    def __init__(self, controller, namespace):
        self._controller = controller
        self._namespace = namespace

    def get_suggestions(self, start):
        return self._namespace.get_suggestions_for(self._controller, start)

    def has_name(self, value):
        for sug in self._namespace.get_suggestions_for(self._controller, value):
            if sug.name == value:
                return True
        return False


class LocalRowNamespace(LocalMacroNamespace):

    def __init__(self, controller, namespace, row):
        LocalMacroNamespace.__init__(self, controller, namespace)
        self._row = row

    def get_suggestions(self, start):
        suggestions = LocalMacroNamespace.get_suggestions(self, start)
        if self._could_be_variable(start):
            suggestions = self._harvest_local_variables(start, suggestions)
        else:
            suggestions = self._harvest_local_variables('${'+start, suggestions)
            suggestions = self._harvest_local_variables('@{'+start, suggestions)
            suggestions = self._harvest_local_variables('&{'+start, suggestions)
        return suggestions

    def _harvest_local_variables(self, start, suggestions):
        matching_assignments = set()
        for row, step in enumerate(self._controller.steps):
            if self._row == row:
                break
            matching_assignments = matching_assignments.union(
                val.replace('=', '').strip() for val in step.assignments if
                val.startswith(start))
        if matching_assignments:
            local_variables = [LocalVariableInfo(name) for name
                               in matching_assignments]
            suggestions = sorted(self._remove_duplicates(suggestions,
                                                         local_variables))
        return suggestions

    def _could_be_variable(self, start):
        return len(start) == 0 or start[0] in ['$', '@', '&']

    def has_name(self, value):
        if self._row is not None:
            for row, step in enumerate(self._controller.steps):
                if self._row == row:
                    break
                if step.is_assigning(value):
                    return True
        return LocalMacroNamespace.has_name(self, value)

    def _remove_duplicates(self, suggestions, local_variables):
        def is_unique(gvar):
            return utils.normalize(gvar.name) not in \
            [utils.normalize(lvar.name) for lvar in local_variables]
        unique = [gvar for gvar in suggestions if is_unique(gvar)]
        return unique + local_variables
