#  Copyright 2025-     Robot Framework Foundation
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
import pytest
import wx
import shutil
import sys
import unittest
from unittest.mock import patch
from pytest import MonkeyPatch
from wx.lib.agw.aui import AuiManager
from wx.lib.agw.buttonpanel import BoxSizer
from .common_setup import MyApp
from multiprocessing import shared_memory
from utest.resources import datafilereader, MessageRecordingLoadObserver
from robotide.publish import PUBLISHER, RideExecuteLibraryInstall, RideOpenLibraryDocumentation
from robotide.spec.libraryfinder import LibraryFinderPlugin
import robotide.spec.libraryfinder
from robotide.ui.mainframe import ActionRegisterer, ToolBar
from robotide.ui.actiontriggers import MenuBar, ShortcutRegistry
from robotide.ui.treeplugin import Tree
from robotide.application import Project
from robotide.robotapi import Variable
from robotide.controller import data_controller
from robotide.controller.settingcontrollers import VariableController
from robotide.controller.tablecontrollers import VariableTableController
from robotide.editor import EditorPlugin, EditorCreator
from robotide.editor.macroeditors import TestCaseEditor
from robotide.editor.settingeditors import ImportSettingListEditor
from robotide.editor.editors import EditorPanel
from robotide.controller.robotdata import new_test_case_file

# Workaround for relative import in non-module
# see https://stackoverflow.com/questions/16981921/relative-imports-in-python-3
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(),
                                              os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

DATADIR = 'fake'
DATAPATH = '%s/path' % DATADIR

try:
    from fakeplugin import FakePlugin
except ImportError:  # Python 3
    from ..editor.fakeplugin import FakePlugin

def close_open_dialogs(evt=None):
    lst = wx.GetTopLevelWindows()
    for i in range(len(lst) - 1, 0, -1):
        dialog = lst[i]
        if isinstance(dialog, wx.Dialog):
            print("Closing " + str(dialog))
            wx.CallAfter(dialog.Close)

def side_effect(args=None):
    return -1


class TestLibraryFinderInstall(unittest.TestCase):

    def setUp(self):
        self.app = MyApp()
        self.settings = self.app.settings
        try:
            self.shared_mem = shared_memory.ShareableList(['en'], name="language")
        except FileExistsError:  # Other instance created file
            self.shared_mem = shared_memory.ShareableList(name="language")
        self.frame = self.app.frame
        self.frame.actions = ActionRegisterer(AuiManager(self.frame), MenuBar(self.frame), ToolBar(self.frame),
                                              ShortcutRegistry(self.frame))
        self.frame.tree = Tree(self.frame, self.frame.actions, self.settings)
        self.app.project = Project(self.app.namespace, self.app.settings)
        self.app.project.load_datafile(datafilereader.TESTCASEFILE_WITH_EVERYTHING, MessageRecordingLoadObserver())
        self.app.model = self.app.project.data
        self.namespace = self.app.project.namespace
        self.controllers = self.app.project.all_testcases()
        self.test_case = next(self.controllers)
        self.suite = self.app.project.suite
        self.plugin = EditorPlugin(self.app)
        self.plugin.add_self_as_tree_aware_plugin()
        self.app.tree.populate(self.app.project)
        self.panel = EditorPanel(self.plugin, self.frame, self.app.project.controller, self.frame.tree)
        self.source = self.app.tree.controller
        sizer = BoxSizer()
        managed_window = self.app._mgr.GetManagedWindow()  # "notebook_editors"
        managed_window.SetSizer(sizer)
        self._grid = ImportSettingListEditor(self.panel, self.frame.tree, self.app.project.controller.imports)
        self.plugin.add_tab(self._grid, 'Editor')
        self.plugin._editor_component = self._grid  # KeywordEditor(self, self.editor, self.app.tree)
        self.app.tree.set_editor(self.plugin._editor_component)
        self.app.tree.populate(self.app.project)
        self.app.frame.SetStatusText("File:" + self.app.project.data.source)
        self._registered_editors = {}
        self.creator = EditorCreator(self._register)
        self.creator.register_editors()
        self.suite = self.app.project.suite
        self.imports = [i for i in self.suite.imports]  # .imports
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        self.frame.Show()
        self.SHOWING = True
        self.frame.Center()
        self.libplugin = LibraryFinderPlugin(self.app)
        # self.frame.notebook = self.app.notebook
        self.libplugin._editor_component = self._grid
        self.libplugin.enable()
        self.libplugin._editor_component.SetSize(wx.Size(800, 600))
        # wx.CallLater(1000, self.app.MainLoop)

    def _register(self, iclass, eclass):
        self._registered_editors[iclass] = eclass

    def _editor_for(self, plugin):
        return self.creator.editor_for(plugin, self.frame, self.app.tree)

    def _datafile_editor(self):
        return self.creator.editor_for(self.plugin, self.frame, self.app.tree)  # self._datafile_plugin(self.app)

    def _datafile_plugin(self, parent):
        # return FakePlugin(self._registered_editors, self._datafile_controller())
        print(f"DEBUG: _datafile_plugin parent={parent}")
        return TestCaseEditor(self.plugin, self._grid, self.test_case, self.app.tree)

    def _variable_plugin(self):
        return FakePlugin(self._registered_editors,
                          VariableController(VariableTableController(
                              self._datafile_controller(), None),
                              Variable(None, '','')))

    def _no_item_selected_plugin(self):
        return FakePlugin(self._registered_editors, None)

    def _datafile_controller(self):
        return data_controller(new_test_case_file(datafilereader.TESTCASEFILE_WITH_EVERYTHING), self.app.project)

    def tearDown(self):
        self.libplugin.disable()
        self.libplugin.unsubscribe_all()
        PUBLISHER.unsubscribe_all()
        self.app.project.close()
        wx.CallAfter(self.app.ExitMainLoop)
        # DEBUG self.app.MainLoop()  # With this here, there is no Segmentation fault
        # wx.CallAfter(wx.Exit)
        self.shared_mem.shm.close()
        self.shared_mem.shm.unlink()
        self.app.Destroy()
        self.app = None
        if os.path.exists(DATADIR):
            shutil.rmtree(DATADIR, ignore_errors=True)

    def test_call_plugin_exec_install(self):
        from time import sleep
        wx.CallLater(8000, self.app.ExitMainLoop)
        wx.CallLater(5000, close_open_dialogs)
        RideExecuteLibraryInstall(item=None).publish()
        sleep(1)
        wx.CallLater(6000, close_open_dialogs)
        RideExecuteLibraryInstall(item="AppiumLibrary").publish()
        self.libplugin._execute_namespace_update()
        command = self.libplugin.find_install_command(None)
        assert command == []
        command = self.libplugin.find_install_command("NonExisting")
        assert command == []
        command = self.libplugin.find_install_command("NoCommand")
        assert command == ['']
        command = self.libplugin.find_install_command("NoDoc")
        assert command == ['%executable -m pip list']
        command = self.libplugin.find_install_command("NoNothing")
        assert command == []
        command = self.libplugin.find_install_command("AppiumLibrary")
        assert command == ['%executable -m pip install -U robotframework-appiumlibrary']

    # @patch('robotide.run.ui.Runner'), mock_input
    def test_call_exec_lib_install(self):
        from robotide.run import ui
        from robotide.pluginapi.plugin import Plugin
        # wx.CallLater(8000, self.app.ExitMainLoop)
        # wx.CallLater(5000, close_open_dialogs)
        def install_side_effect(*args, **kwargs):
            return ['AppiumLibrary',
                    'https://serhatbolsu.github.io/robotframework-appiumlibrary/AppiumLibrary.html',
                    ['%executable -m pip install -U robotframework-appiumlibrary']]

        def dialog_OK(arg):
            return wx.ID_OK

        def dialog_value(arg):
            return '%executable -m pip install -U robotframework-appiumlibrary'

        def statusbar_message(*args, **kwargs):
            pass

        with MonkeyPatch().context() as m:
            m.setattr(robotide.spec.libraryfinder.LibraryFinderPlugin, 'on_library_form', install_side_effect)
            m.setattr(Plugin, 'statusbar_message', statusbar_message)
            m.setattr(ui.Runner, 'run', side_effect)
            m.setattr(wx.TextEntryDialog, 'ShowModal', dialog_OK)
            m.setattr(wx.TextEntryDialog, 'GetValue', dialog_value)
            __ = self.libplugin.execute_library_install('')

    def test_call_exec_lib_install_no_name(self):
        from robotide.run import ui
        from robotide.pluginapi.plugin import Plugin
        # wx.CallLater(8000, self.app.ExitMainLoop)
        # wx.CallLater(5000, close_open_dialogs)
        def install_side_effect(*args, **kwargs):
            return ['',
                    'https://serhatbolsu.github.io/robotframework-appiumlibrary/AppiumLibrary.html',
                    ['%executable -m pip install -U robotframework-appiumlibrary']]

        def dialog_OK(arg):
            return wx.ID_OK

        def dialog_value(arg):
            return '%executable -m pip install -U robotframework-appiumlibrary'

        def statusbar_message(*args, **kwargs):
            pass

        with MonkeyPatch().context() as m:
            m.setattr(robotide.spec.libraryfinder.LibraryFinderPlugin, 'on_library_form', install_side_effect)
            m.setattr(Plugin, 'statusbar_message', statusbar_message)
            m.setattr(ui.Runner, 'run', side_effect)
            m.setattr(wx.TextEntryDialog, 'ShowModal', dialog_OK)
            m.setattr(wx.TextEntryDialog, 'GetValue', dialog_value)
            __ = self.libplugin.execute_library_install('')

    def test_call_exec_lib_install_no_command(self):
        from robotide.run import ui
        from robotide.pluginapi.plugin import Plugin
        # wx.CallLater(8000, self.app.ExitMainLoop)
        # wx.CallLater(5000, close_open_dialogs)
        def install_side_effect(*args, **kwargs):
            return ['NoCommand',
                    'https://serhatbolsu.github.io/robotframework-appiumlibrary/AppiumLibrary.html',
                    '']

        def dialog_OK(arg):
            return wx.ID_OK

        def dialog_value(arg):
            return ''

        def statusbar_message(*args, **kwargs):
            pass

        with MonkeyPatch().context() as m:
            m.setattr(robotide.spec.libraryfinder.LibraryFinderPlugin, 'on_library_form', install_side_effect)
            m.setattr(Plugin, 'statusbar_message', statusbar_message)
            m.setattr(ui.Runner, 'run', side_effect)
            m.setattr(wx.TextEntryDialog, 'ShowModal', dialog_OK)
            m.setattr(wx.TextEntryDialog, 'GetValue', dialog_value)
            __ = self.libplugin.execute_library_install('')

    def test_call_exec_lib_install_find_command(self):
        from robotide.run import ui
        from robotide.pluginapi.plugin import Plugin
        # wx.CallLater(8000, self.app.ExitMainLoop)
        # wx.CallLater(5000, close_open_dialogs)
        def install_side_effect(*args, **kwargs):
            return ['CSVLibrary',
                    'https://rawgit.com/s4int/robotframework-CSVLibrary/master/doc/CSVLibrary.html',
                    ['%executable -m pip install -U robotframework-csvlibrary']]

        def dialog_OK(arg):
            return wx.ID_OK

        def dialog_value(arg):
            return ''

        def pass_side_effect(arg):
            return True

        def statusbar_message(*args, **kwargs):
            pass

        with MonkeyPatch().context() as m:
            m.setattr(robotide.spec.libraryfinder.LibraryFinderPlugin, 'on_library_form', install_side_effect)
            m.setattr(Plugin, 'statusbar_message', statusbar_message)
            m.setattr(ui.Runner, 'run', pass_side_effect)
            m.setattr(wx.TextEntryDialog, 'ShowModal', dialog_OK)
            m.setattr(wx.TextEntryDialog, 'GetValue', dialog_value)
            __ = self.libplugin.execute_library_install('')

    def test_call_exec_lib_install_cancel_find_command(self):
        from robotide.run import ui
        from robotide.pluginapi.plugin import Plugin
        # wx.CallLater(8000, self.app.ExitMainLoop)
        # wx.CallLater(5000, close_open_dialogs)
        def install_side_effect(*args, **kwargs):
            return ['CSVLibrary',
                    'https://rawgit.com/s4int/robotframework-CSVLibrary/master/doc/CSVLibrary.html',
                    ['%executable -m pip install -U robotframework-csvlibrary']]

        def dialog_NotOK(arg):
            return wx.ID_CANCEL

        def dialog_value(arg):
            return ''

        def pass_side_effect(arg):
            return True

        def statusbar_message(*args, **kwargs):
            pass

        with MonkeyPatch().context() as m:
            m.setattr(robotide.spec.libraryfinder.LibraryFinderPlugin, 'on_library_form', install_side_effect)
            m.setattr(Plugin, 'statusbar_message', statusbar_message)
            m.setattr(ui.Runner, 'run', pass_side_effect)
            m.setattr(wx.TextEntryDialog, 'ShowModal', dialog_NotOK)
            m.setattr(wx.TextEntryDialog, 'GetValue', dialog_value)
            __ = self.libplugin.execute_library_install('')

    # @pytest.mark.skip("Investigate why failing.")
    def test_call_exec_lib_install_standard(self):
        # wx.CallLater(8000, self.app.ExitMainLoop)
        def install_side_effect(*args, **kwargs):
            return ['Process', '', '']

        with MonkeyPatch().context() as m:
            m.setattr(robotide.spec.libraryfinder.LibraryFinderPlugin, 'on_library_form', install_side_effect)
            __ = self.libplugin.execute_library_install('')

    @patch('robotide.run.ui.Runner')
    def test_misc_run_install(self, mock_input):
        # wx.CallLater(6000, self.app.ExitMainLoop)
        result = self.libplugin.run_install('NoDoc', ['%executable -m pip list'])
        assert result

    def test_misc_fail_run(self):
        from robotide.run import ui
        # wx.CallLater(6000, self.app.ExitMainLoop)
        with MonkeyPatch().context() as m:
            m.setattr(ui.Runner, 'run', side_effect)
            result = self.libplugin.run_install('NoDoc', ['%executable -m pip list'])
            assert not result
        result = self.libplugin.run_install('', ['%executable -m pip list'])
        assert not result
        result = self.libplugin.run_install('NoCommand', None)
        assert not result

    def test_parser(self):
        # wx.CallLater(6000, self.app.ExitMainLoop)
        self.app.settings.__delattr__('executable')
        exe = sys.executable
        result = self.libplugin.parse_command(['%executable -m pip list'])
        assert result == [f'{exe} -m pip list']
        self.app.settings['executable'] = 'my_python_executable'
        result = self.libplugin.parse_command(['%executable -m pip list'])
        assert result == ['my_python_executable -m pip list']
        result = self.libplugin.parse_command(['some command without python', '%executable -m pip list',
                                               '%executable --version'])
        assert result == ['some command without python', 'my_python_executable -m pip list',
                          'my_python_executable --version']


class TestLibraryFinderDoc(unittest.TestCase):

    def setUp(self):
        self.app = MyApp()
        self.settings = self.app.settings
        try:
            self.shared_mem = shared_memory.ShareableList(['en'], name="language")
        except FileExistsError:  # Other instance created file
            self.shared_mem = shared_memory.ShareableList(name="language")
        self.frame = self.app.frame
        self.frame.actions = ActionRegisterer(AuiManager(self.frame), MenuBar(self.frame), ToolBar(self.frame),
                                              ShortcutRegistry(self.frame))
        self.frame.tree = Tree(self.frame, self.frame.actions, self.settings)
        self.app.project = Project(self.app.namespace, self.app.settings)
        self.app.project.load_datafile(datafilereader.TESTCASEFILE_WITH_EVERYTHING, MessageRecordingLoadObserver())
        self.app.model = self.app.project.data
        self.namespace = self.app.project.namespace
        self.controllers = self.app.project.all_testcases()
        self.test_case = next(self.controllers)
        self.suite = self.app.project.suite
        self.plugin = EditorPlugin(self.app)
        self.plugin.add_self_as_tree_aware_plugin()
        self.app.tree.populate(self.app.project)
        self.panel = EditorPanel(self.plugin, self.frame, self.app.project.controller, self.frame.tree)
        self.source = self.app.tree.controller
        sizer = BoxSizer()
        managed_window = self.app._mgr.GetManagedWindow()  # "notebook_editors"
        managed_window.SetSizer(sizer)
        self._grid = ImportSettingListEditor(self.panel, self.frame.tree, self.app.project.controller.imports)
        self.plugin.add_tab(self._grid, 'Editor')
        self.plugin._editor_component = self._grid  # KeywordEditor(self, self.editor, self.app.tree)
        self.app.tree.set_editor(self.plugin._editor_component)
        self.app.tree.populate(self.app.project)
        self.app.frame.SetStatusText("File:" + self.app.project.data.source)
        self._registered_editors = {}
        self.creator = EditorCreator(self._register)
        self.creator.register_editors()
        self.suite = self.app.project.suite
        self.imports = [i for i in self.suite.imports]  # .imports
        # Uncomment next line (and MainLoop in tests) if you want to see the app
        self.frame.Show()
        self.SHOWING = True
        self.frame.Center()
        self.libplugin = LibraryFinderPlugin(self.app)
        # self.frame.notebook = self.app.notebook
        self.libplugin._editor_component = self._grid
        self.libplugin.enable()
        self.libplugin._editor_component.SetSize(wx.Size(800, 600))
        # wx.CallLater(1000, self.app.MainLoop)

    def _register(self, iclass, eclass):
        self._registered_editors[iclass] = eclass

    def _editor_for(self, plugin):
        return self.creator.editor_for(plugin, self.frame, self.app.tree)

    def _datafile_editor(self):
        return self.creator.editor_for(self.plugin, self.frame, self.app.tree)  # self._datafile_plugin(self.app)

    def _datafile_plugin(self, parent):
        # return FakePlugin(self._registered_editors, self._datafile_controller())
        print(f"DEBUG: _datafile_plugin parent={parent}")
        return TestCaseEditor(self.plugin, self._grid, self.test_case, self.app.tree)

    def _variable_plugin(self):
        return FakePlugin(self._registered_editors,
                          VariableController(VariableTableController(
                              self._datafile_controller(), None),
                              Variable(None, '','')))

    def _no_item_selected_plugin(self):
        return FakePlugin(self._registered_editors, None)

    def _datafile_controller(self):
        return data_controller(new_test_case_file(datafilereader.TESTCASEFILE_WITH_EVERYTHING), self.app.project)

    def tearDown(self):
        self.libplugin.disable()
        self.libplugin.unsubscribe_all()
        PUBLISHER.unsubscribe_all()
        self.app.project.close()
        wx.CallAfter(self.app.ExitMainLoop)
        # DEBUG self.app.MainLoop()  # With this here, there is no Segmentation fault
        # wx.CallAfter(wx.Exit)
        self.shared_mem.shm.close()
        self.shared_mem.shm.unlink()
        self.app.Destroy()
        self.app = None
        if os.path.exists(DATADIR):
            shutil.rmtree(DATADIR, ignore_errors=True)


    @patch('wx.LaunchDefaultBrowser')
    def test_call_plugin_doc(self, mock_input):
        from time import sleep
        wx.CallLater(8000, self.app.ExitMainLoop)
        wx.CallLater(5000, close_open_dialogs)
        RideOpenLibraryDocumentation(item=None).publish()
        sleep(1)
        wx.CallLater(6000, close_open_dialogs)
        RideOpenLibraryDocumentation(item="RequestsLibrary").publish()
        documentation = self.libplugin.find_documentation_url(None)
        assert documentation == ''
        documentation = self.libplugin.find_documentation_url("NonExisting")
        assert documentation == ''
        documentation = self.libplugin.find_documentation_url("NoDoc")
        assert documentation == ''
        documentation = self.libplugin.find_documentation_url("NoNothing")
        assert documentation == ''
        documentation = self.libplugin.find_documentation_url("NoCommand")
        assert documentation == 'https://robotframework.org'
        documentation = self.libplugin.find_documentation_url("RequestsLibrary")
        assert documentation == 'https://marketsquare.github.io/robotframework-requests/doc/RequestsLibrary.html'
        documentation = self.libplugin.find_documentation_url("Remote")
        assert documentation == 'https://github.com/robotframework/RemoteInterface'
        documentation = self.libplugin.find_documentation_url("Collections")
        assert documentation == 'https://robotframework.org/robotframework/latest/libraries/Collections.html'

    @patch('wx.LaunchDefaultBrowser')
    def test_call_open_doc_valid(self, mock_input):
        def doc_side_effect(*args, **kwargs):
            return ['RequestsLibrary',
                    'https://marketsquare.github.io/robotframework-requests/doc/RequestsLibrary.html',
                    'some command without python | %executable -m pip install -U robotframework-requests']

        # wx.CallLater(8000, self.app.ExitMainLoop)
        # wx.CallLater(5000, close_open_dialogs)
        with MonkeyPatch().context() as m:
            m.setattr(robotide.spec.libraryfinder.LibraryFinderPlugin, 'on_library_form', doc_side_effect)
            __ = self.libplugin.open_library_documentation('')

    @patch('wx.LaunchDefaultBrowser')
    def test_call_open_doc_not_valid(self, mock_input):
        def doc_side_effect(*args, **kwargs):
            return ['RequestsLibrary', '',
                    ['some command without python', '%executable -m pip install -U robotframework-requests',
                     'my_python_executable --version']]

        def dialog_OK(arg):
            return wx.ID_OK

        def dialog_value(arg):
            return 'https://marketsquare.github.io/robotframework-requests/doc/RequestsLibrary.html'

        # wx.CallLater(8000, self.app.ExitMainLoop)
        # wx.CallLater(5000, close_open_dialogs)
        with MonkeyPatch().context() as m:
            m.setattr(robotide.spec.libraryfinder.LibraryFinderPlugin, 'on_library_form', doc_side_effect)
            m.setattr(wx.TextEntryDialog, 'ShowModal', dialog_OK)
            m.setattr(wx.TextEntryDialog, 'GetValue', dialog_value)
            __ = self.libplugin.open_library_documentation('')

    @patch('wx.LaunchDefaultBrowser')
    def test_call_open_doc_canceled_not_valid(self, mock_input):
        def doc_side_effect(*args, **kwargs):
            return ['', '', '']

        def dialog_NotOK(arg):
            return wx.ID_CANCEL

        def dialog_value(arg):
            return ''

        # wx.CallLater(8000, self.app.ExitMainLoop)
        # wx.CallLater(5000, close_open_dialogs)
        with MonkeyPatch().context() as m:
            m.setattr(robotide.spec.libraryfinder.LibraryFinderPlugin, 'on_library_form', doc_side_effect)
            m.setattr(wx.TextEntryDialog, 'ShowModal', dialog_NotOK)
            m.setattr(wx.TextEntryDialog, 'GetValue', dialog_value)
            __ = self.libplugin.open_library_documentation('')

    # @pytest.mark.skip("Investigate why failing.")
    @patch('wx.LaunchDefaultBrowser')
    def test_call_open_doc_standard(self, mock_input):
        def doc_side_effect(*args, **kwargs):
            return ['Collections',
                    'https://robotframework.org/robotframework/latest/libraries/Collections.html',
                    '']

        # wx.CallLater(8000, self.app.ExitMainLoop)
        # wx.CallLater(5000, close_open_dialogs)
        with MonkeyPatch().context() as m:
            m.setattr(robotide.spec.libraryfinder.LibraryFinderPlugin, 'on_library_form', doc_side_effect)
            __ = self.libplugin.open_library_documentation('')


if __name__ == '__main__':
    unittest.main()
