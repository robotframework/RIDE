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


from robotide.controller import Project
from robotide.controller.dataloader import TestDataDirectoryWithExcludes
from robotide.controller.filecontrollers import ExcludedDirectoryController
from robotide.controller.settingcontrollers import VariableController
from robotide import robotapi

from .editors import (
    InitFileEditor, TestCaseFileEditor, WelcomePage, ResourceFileEditor)
from .macroeditors import TestCaseEditor, UserKeywordEditor


def VariableEditorChooser(plugin, parent, controller, tree):
    controller = controller.datafile_controller
    editor_class = plugin.get_editor(controller.data.__class__)
    return editor_class(plugin, parent, controller, tree)


class EditorCreator(object):
    # TODO: Should not use robot.model classes here
    _EDITORS = ((robotapi.TestDataDirectory, InitFileEditor),
                (robotapi.ResourceFile, ResourceFileEditor),
                (robotapi.TestCase, TestCaseEditor),
                (robotapi.TestCaseFile, TestCaseFileEditor),
                (robotapi.UserKeyword, UserKeywordEditor),
                (robotapi.Variable, VariableEditorChooser),
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
        controller = plugin.get_selected_item()
        if self._invalid(controller):
            # http://code.google.com/p/robotframework-ride/issues/detail?id=1092
            if self._editor and tree and (not tree._datafile_nodes or
                                          self._only_resource_files(tree)):
                self._editor.destroy()
                self._editor = None
                return None
            if self._editor:
                return self._editor
            return WelcomePage(editor_panel)
        if self._should_use_old_editor(controller):
            return self._editor
        return self._create_new_editor(controller, editor_panel, plugin, tree)

    def _invalid(self, controller):
        return not controller or controller.data is None or \
            isinstance(controller, Project) or \
            isinstance(controller, ExcludedDirectoryController)

    def _should_use_old_editor(self, controller):
        return self._editor and \
            isinstance(controller, VariableController) and \
            controller.datafile_controller is self._editor.controller

    def _create_new_editor(self, controller, editor_panel, plugin, tree):
        editor_class = plugin.get_editor(controller.data.__class__)
        if self._editor:
            self._editor.destroy()
        editor_panel.Show(False)
        return editor_class(plugin, editor_panel, controller, tree)

    def _only_resource_files(self, tree):
        return all([tree.node_is_resource_file(node)
                    for node in tree._datafile_nodes])
