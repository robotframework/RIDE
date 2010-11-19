#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

class _BaseController(object):

    @property
    def display_name(self):
        return self.data.name

    def execute(self, command):
        return command.execute(self)

class ControllerWithParent(object):

    def mark_dirty(self):
        if self._parent:
            self._parent.mark_dirty()

    @property
    def dirty(self):
        return self._parent.dirty

    @property
    def datafile_controller(self):
        return self._parent.datafile_controller

    @property
    def datafile(self):
        return self._parent.datafile

    @property
    def all_datafiles(self):
        return self._parent.all_datafiles


class WithUndoRedoStacks(object):

    @property
    def _undo(self):
        if not hasattr(self, '_undo_stack'):
            self._undo_stack = []
        return self._undo_stack

    @property
    def _redo(self):
        if not hasattr(self, '_redo_stack'):
            self._redo_stack = []
        return self._redo_stack

    def clear_undo(self):
        self._undo_stack = []

    def is_undo_empty(self):
        return self._undo == []

    def pop_from_undo(self):
        return self._undo.pop()

    def push_to_undo(self, command):
        self._undo.append(command)

    def clear_redo(self):
        self._redo_stack = []

    def is_redo_empty(self):
        return self._redo == []

    def pop_from_redo(self):
        return self._redo.pop()

    def push_to_redo(self, command):
        self._redo.append(command)
