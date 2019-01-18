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

from robotide.publish.messages import RideModificationPrevented


class _BaseController(object):

    @property
    def display_name(self):
        return self.data.name

    def execute(self, command):
        if not command.modifying or self.is_modifiable():
            return command.execute(self)
        else:
            RideModificationPrevented(controller=self).publish()

    def is_modifiable(self):
        return True

    def is_excluded(self):
        return False


class ControllerWithParent(_BaseController):

    @property
    def parent(self):
        return self._parent

    def set_parent(self, new_parent):
        self._parent = new_parent

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
    def datafiles(self):
        return self._parent.datafiles

    def is_modifiable(self):
        return self.datafile_controller.is_modifiable()


class WithNamespace(object):
    _namespace = None # Ensure namespace exists

    def _set_namespace_from(self, controller):
        self._set_namespace(controller._namespace)

    def _set_namespace(self, namespace):
        self._namespace = namespace

    def update_namespace(self):
        if not self._namespace:
            return
        self._namespace.update()

    def register_for_namespace_updates(self, listener):
        if not self._namespace:
            return
        self._namespace.register_update_listener(listener)

    def unregister_namespace_updates(self, listener):
        if not self._namespace:
            return
        self._namespace.unregister_update_listener(listener)

    def clear_namespace_update_listeners(self):
        self._namespace.clear_update_listeners()

    def is_user_keyword(self, datafile, value):
        return self._namespace.is_user_keyword(datafile, value)

    def is_library_keyword(self, datafile, value):
        return self._namespace.is_library_keyword(datafile, value)

    def get_all_keywords_from(self, *datafiles):
        return self._namespace.get_all_keywords(*datafiles)

    def get_all_cached_library_names(self):
        return self._namespace.get_all_cached_library_names()

    def keyword_info(self, datafile, keyword_name):
        return self._namespace.find_keyword(datafile, keyword_name)

    def is_library_import_ok(self, imp):
        return self._namespace.is_library_import_ok(self.datafile, imp)

    def is_variables_import_ok(self, imp):
        # print("DEBUG: BaseController is_variables_import_ok %s\n" % imp.name)
        return self._namespace.is_variables_import_ok(self.datafile, imp)


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
