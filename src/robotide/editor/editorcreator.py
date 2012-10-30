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


from robot.parsing.model import (TestCase, TestDataDirectory, ResourceFile,
        TestCaseFile, UserKeyword, Variable)

from robotide.controller.chiefcontroller import ChiefController
from robotide.controller.dataloader import TestDataDirectoryWithExcludes
from robotide.controller.settingcontrollers import VariableController

from .editors import (InitFileEditor, TestCaseFileEditor, WelcomePage,
        ResourceFileEditor)
from .macroeditors import TestCaseEditor, UserKeywordEditor


def VariableEditorChooser(plugin, parent, controller, tree):
    controller = controller.datafile_controller
    editor_class = plugin.get_editor(controller.data.__class__)
    return editor_class(plugin, parent, controller, tree)


class EditorCreator(object):
    # TODO: Should not use robot.model classes here
    _EDITORS = ((TestDataDirectory, InitFileEditor),
                (ResourceFile, ResourceFileEditor),
                (TestCase, TestCaseEditor),
                (TestCaseFile, TestCaseFileEditor),
                (UserKeyword, UserKeywordEditor),
                (Variable, VariableEditorChooser),
                (TestDataDirectoryWithExcludes, InitFileEditor))

    def __init__(self, editor_registerer):
        self._editor_registerer = editor_registerer
        self._editor = None

    def register_editors(self):
        for item, editorclass in self._EDITORS:
            self._editor_registerer(item, editorclass)

    def editor_for(self, plugin, editor_panel, tree):
        controller = plugin.get_selected_item()
        if not controller or not controller.data or isinstance(controller, ChiefController):
            if self._editor:
                return self._editor
            self._editor = WelcomePage(editor_panel)
            return self._editor
        if self._editor and isinstance(controller, VariableController) and controller.datafile_controller is self._editor.controller:
            return self._editor
        editor_class = plugin.get_editor(controller.data.__class__)
        if self._editor:
            self._editor.destroy()
        editor_panel.Show(False)
        self._editor = editor_class(plugin, editor_panel, controller, tree)
        return self._editor
