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
from .. import controller
from ..controller.dataloader import TestDataDirectoryWithExcludes
from ..controller import filecontrollers
from ..controller.settingcontrollers import VariableController
from .editors import (InitFileEditor, TestCaseFileEditor, WelcomePage, ResourceFileEditor)
from .macroeditors import TestCaseEditor, UserKeywordEditor


def variable_editor_chooser(plugin, parent, _controller, tree):
    _controller = _controller.datafile_controller
    editor_class = plugin.get_editor(_controller.data.__class__)
    return editor_class(plugin, parent, _controller, tree)


class EditorCreator(object):
    # DEBUG: Should not use robot.model classes here
    _EDITORS = ((robotapi.TestDataDirectory, InitFileEditor),
                (robotapi.ResourceFile, ResourceFileEditor),
                (robotapi.TestCase, TestCaseEditor),
                (robotapi.TestCaseFile, TestCaseFileEditor),
                (robotapi.UserKeyword, UserKeywordEditor),
                (robotapi.Variable, variable_editor_chooser),
                (TestDataDirectoryWithExcludes, InitFileEditor))

    def __init__(self, editor_registerer):
        self._editor_registerer = editor_registerer
        self._editor = None

    def register_editors(self):
        for item, editorclass in self._EDITORS:
            self._editor_registerer(item, editorclass)

    def editor_for(self, plugin, editor_panel, tree):
        self._editor = self._create_editor(editor_panel, plugin, tree)
        return self._editor

    def _create_editor(self, editor_panel, plugin, tree):
        _controller = plugin.get_selected_item()
        if self._invalid(_controller):
            # http://code.google.com/p/robotframework-ride/issues/detail?id=1092
            if self._editor and tree and (not tree.datafile_nodes or
                                          self._only_resource_files(tree)):
                self._editor.w_destroy()
                self._editor = None
                return None
            if self._editor:
                return self._editor
            return WelcomePage(editor_panel)
        if self._should_use_old_editor(_controller):
            return self._editor
        return self._create_new_editor(_controller, editor_panel, plugin, tree)

    @staticmethod
    def _invalid(_controller):
        return not _controller or _controller.data is None or \
               isinstance(_controller, controller.Project) or \
               isinstance(_controller, filecontrollers.ExcludedDirectoryController)

    def _should_use_old_editor(self, _controller):
        return self._editor and \
            isinstance(_controller, VariableController) and \
            _controller.datafile_controller is self._editor.controller

    def _create_new_editor(self, _controller, editor_panel, plugin, tree):
        editor_class = plugin.get_editor(_controller.data.__class__)
        if self._editor:
            self._editor.w_destroy()
        editor_panel.Show(False)
        return editor_class(plugin, editor_panel, _controller, tree)

    @staticmethod
    def _only_resource_files(tree):
        return all([tree.node_is_resource_file(node)
                    for node in tree.datafile_nodes])
