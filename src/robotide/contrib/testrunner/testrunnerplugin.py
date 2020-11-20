# -*- encoding: utf-8 -*-
# Copyright 2010 Orbitz WorldWide
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Modified by NSN
#  Copyright 2010-2012 Nokia Solutions and Networks
#  Copyright 2013-2015 Nokia Networks
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

"""A plugin for running tests from within RIDE

Some icons courtesy Mark James and provided under a creative commons
license.  See http://www.famfamfam.com/lab/icons/silk

Note: this plugin creates a temporary directory for use while a test
is running. This directory is normally removed when RIDE exists. If
RIDE is shut down abnormally this directory may not get removed. The
directories that are created match the pattern RIDE*.d and are in a
temporary directory appropriate for the platform (for example, on
linux it's /tmp).

You can safely manually remove these directories, except for the one
being used for a currently running test.
"""
import atexit
import datetime
import shutil
import subprocess
import tempfile
import threading
import time
import os
import psutil
import re
import wx
import wx.stc
from functools import reduce
from queue import Queue
from wx.lib.embeddedimage import PyEmbeddedImage

from robotide.action.shortcut import localize_shortcuts
from robotide.context import IS_WINDOWS, IS_MAC
from robotide.contrib.testrunner import TestRunner
from robotide.contrib.testrunner import runprofiles
from robotide.contrib.testrunner.ArgsParser import ArgsParser
from robotide.contrib.testrunner.CommandArgsBuilder import CommandArgsBuilder
from robotide.contrib.testrunner.CommandBuilder import CommandBuilder
from robotide.contrib.testrunner.FileWriter import FileWriter
from robotide.contrib.testrunner.SettingsParser import SettingsParser
from robotide.controller.macrocontrollers import TestCaseController
from robotide.publish import RideSettingsChanged, PUBLISHER
from robotide.publish.messages import RideTestSelectedForRunningChanged
from robotide.pluginapi import Plugin, ActionInfo
from robotide.ui.notebook import NoteBook
from robotide.widgets import Label, ImageProvider
from robotide.robotapi import LOG_LEVELS
from robotide.utils import robottime
from robotide.preferences.editors import ReadFonts
from sys import getfilesystemencoding
from robotide.lib.robot.utils.encodingsniffer import (get_console_encoding,
                                                      get_system_encoding)

CONSOLE_ENCODING = get_console_encoding()
SYSTEM_ENCODING = get_system_encoding()
OUTPUT_ENCODING = getfilesystemencoding()
encoding = {'CONSOLE': CONSOLE_ENCODING,
            'SYSTEM': SYSTEM_ENCODING,
            'OUTPUT': OUTPUT_ENCODING}

ID_RUN = wx.NewIdRef()
ID_RUNDEBUG = wx.NewIdRef()
ID_STOP = wx.NewIdRef()
ID_PAUSE = wx.NewIdRef()
ID_CONTINUE = wx.NewIdRef()
ID_STEP_NEXT = wx.NewIdRef()
ID_STEP_OVER = wx.NewIdRef()
ID_OPEN_LOGS_DIR = wx.NewId()
ID_SHOW_REPORT = wx.NewIdRef()
ID_SHOW_LOG = wx.NewIdRef()
ID_AUTOSAVE = wx.NewIdRef()
ID_PAUSE_ON_FAILURE = wx.NewIdRef()
ID_SHOW_MESSAGE_LOG = wx.NewIdRef()
STYLE_DEFAULT = 0
STYLE_STDERR = 2
ATEXIT_LOCK = threading.RLock()


def _RunProfile(name, run_prefix):
    return type('Profile', (runprofiles.PybotProfile,),
                {'name': name, 'get_command': lambda self: run_prefix})


class TestRunnerPlugin(Plugin):
    """A plugin for running tests from within RIDE"""
    defaults = {"auto_save": False,
                "confirm run": True,
                "profile": "robot",
                "sash_position": 200,
                "run_profiles":
                    [('jybot', 'jybot' + ('.bat' if os.name == 'nt' else '')),
                     ('pybot', 'pybot' + ('.bat' if os.name == 'nt' else '')),
                     ('robot 3.1', 'robot')],
                "font size": 10,
                "font face": 'Courier New',
                "foreground": 'black',
                "background": 'white',
                "error": 'red'}

    report_regex = re.compile("^Report: {2}(.*\.html)$", re.MULTILINE)
    log_regex = re.compile("^Log: {5}(.*\.html)$", re.MULTILINE)
    title = "Run"

    def __init__(self, application=None):
        Plugin.__init__(self, application, initially_enabled=True,
                        default_settings=self.defaults)
        self.version = "3.1"
        self.metadata = {
            "url":
            "https://github.com/robotframework/RIDE/wiki/Test-Runner-Plugin"}
        self._reload_timer = None
        self._frame = application.frame
        self._report_file = None
        self._log_file = None
        self._controls = {}
        self._running = False
        self._currently_executing_keyword = None
        self._test_runner = TestRunner(application.model)
        self._register_shortcuts()
        self._min_log_level_number = LOG_LEVELS['INFO']
        self._pause_on_failure = False
        self._selected_tests: {TestCaseController} = set()
        self._process = psutil.Process()
        self._initmemory = None
        self._limitmemory = None  # This will be +80%
        self._maxmemmsg = None

    @property
    def _names_to_run(self):
        return list(
            map(lambda ctrl: (ctrl.datafile_controller.longname, ctrl.longname),
                self._selected_tests))

    def _register_shortcuts(self):
        self.register_shortcut('CtrlCmd-C', self._copy_from_log_ctrls)
        self.register_shortcut('CtrlCmd-L', self.OnShowLog)
        self.register_shortcut('CtrlCmd-R', self.OnShowReport)
        if IS_WINDOWS or IS_MAC:
            self.register_shortcut('Del', self._delete_pressed)

    def _delete_pressed(self, event):
        if self.notebook.current_page_title != self.title:
            return
        self.get_current_profile().delete_pressed()

    def _copy_from_log_ctrls(self, event):
        if self.notebook.current_page_title != self.title:
            return
        if self._console_log_ctrl.GetSTCFocus():
            self._console_log_ctrl.Copy()
            return
        if self._message_log_ctrl.GetSTCFocus():
            self._message_log_ctrl.Copy()

    def enable(self):
        self.tree.set_checkboxes_for_tests()
        self._read_run_profiles()
        self._register_actions()
        self._add_tab_to_notebook()
        self._init_profile_choice(self.profile_name)
        self._subscribe_to_events()
        self._test_runner.enable(self._test_runner_events_handler)
        self._set_stopped()
        self._create_temporary_directory()

    def _register_actions(self):
        run_action_info = ActionInfo("Tools", "Run Tests", self.OnRun, None,
                                     "F8", ImageProvider().TOOLBAR_PLAY,
                                     "Run the selected tests", position=10)
        self._run_action = self.register_action(run_action_info)
        run_action_debug = ActionInfo("Tools", "Run Tests with Debug",
                                      self.OnRunDebug, None,
                                      "F9", getBugIconBitmap(),
                                      "Run the selected tests with Debug",
                                      position=8)
        self._run_action = self.register_action(run_action_debug)
        stop_action_info = ActionInfo("Tools", "Stop Test Run", self.OnStop,
                                      None, "CtrlCmd-F8",
                                      ImageProvider().TOOLBAR_STOP,
                                      "Stop a running test", position=11)
        self._stop_action = self.register_action(stop_action_info)

    def _read_run_profiles(self):
        self._read_run_profiles_from_config()
        self._read_run_profiles_from_classes()

    def _read_run_profiles_from_config(self):
        # Have to keep reference so that these classes are not garbage collected
        self._profile_classes_from_config = [_RunProfile(name, run_prefix)
                                             for name, run_prefix in
                                             self.run_profiles]

    def _read_run_profiles_from_classes(self):
        for profile in self._get_all_subclasses(runprofiles.BaseProfile):
            self._test_runner.add_profile(profile.name, profile(plugin=self))

    def _get_all_subclasses(self, class_):
        classes = []
        for sub_class in class_.__subclasses__():
            classes += [sub_class] + self._get_all_subclasses(sub_class)
        return classes

    def _subscribe_to_events(self):
        self.subscribe(self.OnTestSelectedForRunningChanged,
                       RideTestSelectedForRunningChanged)
        self.subscribe(self.OnSettingsChanged, RideSettingsChanged)

    def OnSettingsChanged(self, message):
        """Updates settings"""
        section, setting = message.keys
        # print("DEBUG: enter OnSettingsChanged section %s" % (section))
        if section == 'Test Run':  # DEBUG temporarily we have two sections
            # print("DEBUG: setting.get('confirm run')= %s " % setting)
            # print("DEBUG: new data= %s old %s new %s" % (data.keys, data.old, data.new))
            self.defaults.setdefault(setting, message.new)
            self.save_setting(setting, message.new)

    def OnTestSelectedForRunningChanged(self, message):
        self._selected_tests = message.tests

    def disable(self):
        self._remove_from_notebook()
        self._test_runner.clear_server()
        self.unsubscribe_all()
        self.unregister_actions()

    def _create_temporary_directory(self):
        self._default_output_dir = tempfile.mkdtemp(".d", "RIDE")
        atexit.register(self._remove_temporary_directory)
        # this plugin creates a temporary directory which _should_
        # get reaped at exit. Sometimes things happen which might
        # cause it to not get deleted. Maybe this would be a good
        # place to check for temporary directories that match the
        # signature and delete them if they are more than a few
        # days old...

    def _remove_temporary_directory(self):
        with ATEXIT_LOCK:
            if os.path.exists(self._default_output_dir):
                shutil.rmtree(self._default_output_dir)

    def OnClose(self, event):
        """Shut down the running services and processes"""
        self._test_runner.kill_process()
        if self._process_timer:
            self._process_timer.Stop()
        self._test_runner.shutdown_server()
        event.Skip()

    def _reset_memory_calc(self):
        self._initmemory = self._process.memory_info()[0]
        self._limitmemory = self._initmemory * 1.80
        self._maxmemmsg = None

    def OnStop(self, event):
        """Called when the user clicks the "Stop" button

        This sends a SIGINT to the running process, with the
        same effect as typing control-c when running from the
        command line."""
        self._reset_memory_calc()
        self._append_to_console_log('[ SENDING STOP SIGNAL ]\n',
                                    source='stderr')
        self._test_runner.send_stop_signal()

    def OnPause(self, event):
        self._reset_memory_calc()
        self._append_to_console_log('[ SENDING PAUSE SIGNAL ]\n')
        self._test_runner.send_pause_signal()

    def OnContinue(self, event):
        self._reset_memory_calc()
        self._append_to_console_log('[ SENDING CONTINUE SIGNAL ]\n')
        self._test_runner.send_continue_signal()

    def OnStepNext(self, event):
        self._reset_memory_calc()
        self._append_to_console_log('[ SENDING STEP NEXT SIGNAL ]\n')
        self._test_runner.send_step_next_signal()

    def OnStepOver(self, event):
        self._reset_memory_calc()
        self._append_to_console_log('[ SENDING STEP OVER SIGNAL ]\n')
        self._test_runner.send_step_over_signal()

    def OnRun(self, event):
        """ Called when the user clicks or presses the F8, Run Tests """
        self._run_tests(lambda: self._create_command())

    def OnRunDebug(self, event):
        """ Called when the user clicks or presses the F9, Run Tests with Debug
            It can still be overwritten in RIDE Arguments line
        """
        self._run_tests(lambda: self._create_command("DEBUG"))

    def _create_command(self, log_level="INFO"):
        profile = self.get_current_profile()
        args = self._create_command_args(
            profile.get_command_args(),
            log_level,
            self._default_output_dir,
            self.global_settings.get('pythonpath', None),
            self._get_console_width(),
            self._names_to_run
        )

        self._min_log_level_number = \
            ArgsParser.get_message_log_level(args)

        self._logs_directory = \
            ArgsParser.get_output_directory(args, self._default_output_dir)

        console_log_name = \
            SettingsParser.get_console_log_name(profile.get_settings())
        self._console_log = '' if not console_log_name \
            else os.path.join(self._logs_directory, console_log_name)

        command_builder = CommandBuilder()
        command_builder.set_prefix(profile.get_command())
        arg_file = os.path.join(self._default_output_dir, 'argfile.txt')
        command_builder.add_arg_file(arg_file, args)
        command_builder.set_listener(self._test_runner.get_listener_port(),
                                     self._pause_on_failure)
        command_builder.set_suite_source(self.model.suite.source)

        return command_builder.build()

    @staticmethod
    def _create_command_args(profile_custom_args, log_level, output_dir,
                             python_path, console_width, tests_to_run):
        args_builder = CommandArgsBuilder(profile_custom_args)

        args_builder.set_log_level(log_level)
        args_builder.set_output_directory(output_dir)
        args_builder.set_python_path(python_path)
        args_builder.without_console_color()
        args_builder.set_console_width(console_width)
        args_builder.set_tests_to_run(tests_to_run)

        return args_builder.build()

    def _run_tests(self, create_command_func):
        if not self._can_start_running_tests():
            return
        if self.__getattr__('confirm run') \
                and not self._tests_selected() \
                and not self._ask_user_to_run_anyway():
            # In Linux NO runs dialog 4 times
            return
        self._reset_memory_calc()
        self._initialize_ui_for_running()
        command = create_command_func()
        # DEBUG on Py3 it not shows correct if tags with latin chars
        self._append_to_console_log("command: %s\n" % command, enc=False)
        try:
            self._test_runner.run_command(command,
                                          self._get_current_working_dir())
            self._process_timer.Start(41)  # roughly 24fps
            self._set_running()
            self._progress_bar.Start()
        except Exception as e:
            self._set_stopped()
            error, log_message = self.get_current_profile().format_error(str(e),
                                                                         None)
            self._append_to_console_log(error, source='stderr')
            if log_message:
                log_message.publish()

    def _get_current_working_dir(self):
        profile = self.get_current_profile()
        if profile.name == runprofiles.CustomScriptProfile.name:
            return profile.get_cwd()
        if not os.path.isdir(self.model.suite.source):
            return os.path.dirname(self.model.suite.source)
        return self.model.suite.source

    def _can_start_running_tests(self):
        if self._running or self.model.suite is None:
            return False
        if not self.is_unsaved_changes():
            return True
        if self.auto_save or self._ask_user_to_save_before_running():
            self.save_all_unsaved_changes()
            return True
        return False

    @staticmethod
    def _ask_user_to_save_before_running(self):
        ret = wx.MessageBox("""There are unsaved modifications.
        Do you want to save all changes and run the tests?""",
                            "Unsaved Modifications",
                            wx.ICON_QUESTION | wx.YES_NO)
        return ret == wx.YES

    def _tests_selected(self):
        return len(self._selected_tests) != 0

    @staticmethod
    def _ask_user_to_run_anyway():
        ret = wx.MessageBox('No tests selected. \n'
                            'Continue anyway?',
                            'No tests selected',
                            wx.ICON_QUESTION | wx.YES_NO)
        return ret == wx.YES

    def _initialize_ui_for_running(self):
        self._show_notebook_tab()
        self._clear_log_ctrls()
        self._local_toolbar.EnableTool(ID_OPEN_LOGS_DIR, False)
        self._local_toolbar.EnableTool(ID_SHOW_REPORT, False)
        self._local_toolbar.EnableTool(ID_SHOW_LOG, False)
        self._report_file = self._log_file = None
        self._log_message_queue = Queue()

    def _clear_log_ctrls(self):
        self._clear_text_ctrl(self._console_log_ctrl)
        self._clear_text_ctrl(self._message_log_ctrl)

    @staticmethod
    def _clear_text_ctrl(textctrl):
        textctrl.SetReadOnly(False)
        textctrl.ClearAll()
        textctrl.SetReadOnly(True)

    def OnOpenLogsDirectory(self, evt):
        """Called when the user clicks on the "Open Logs Directory" button"""
        if os.path.exists(self._logs_directory):
            subprocess.run(['explorer', self._logs_directory])
        else:
            self._notify_user_no_logs_directory()

    def OnShowReport(self, evt):
        """Called when the user clicks on the "Report" button"""
        if self._report_file:
            wx.LaunchDefaultBrowser(
                "file:%s" % os.path.abspath(self._report_file))

    def OnShowLog(self, evt):
        """Called when the user clicks on the "Log" button"""
        if self._log_file:
            wx.LaunchDefaultBrowser("file:%s" % os.path.abspath(self._log_file))

    def OnProcessEnded(self, evt):
        output, errors, log_message = self._test_runner.get_output_and_errors(
            self.get_current_profile())
        self._append_to_console_log(output)
        self._read_report_and_log_from_stdout_if_needed()
        if len(errors) > 0:
            self._append_to_console_log(errors, source="stderr")
        if self._process_timer:
            self._process_timer.Stop()
        self._set_stopped()
        self._progress_bar.Stop()
        now = datetime.datetime.now().timetuple()
        self._append_to_console_log("\nTest finished {}"
                                    .format(robottime.format_time(now)))
        self._test_runner.command_ended()
        if log_message:
            log_message.publish()
        self._local_toolbar.EnableTool(ID_OPEN_LOGS_DIR, True)

    def _read_report_and_log_from_stdout_if_needed(self):
        output = self._console_log_ctrl.GetText()
        if not self._report_file:
            self._report_file = \
                self._get_report_or_log(output, self.report_regex)
            if self._report_file:
                self._local_toolbar.EnableTool(ID_SHOW_REPORT, True)
        if not self._log_file:
            self._log_file = self._get_report_or_log(output, self.log_regex)
            if self._log_file:
                self._local_toolbar.EnableTool(ID_SHOW_LOG, True)

    @staticmethod
    def _get_report_or_log(output, regex):
        res = regex.search(output)
        return res.group(1) if res and os.path.isfile(res.group(1)) else None

    def OnTimer(self, evt):
        """Get process output"""
        if not self._log_message_queue.empty():
            if self._process.memory_info()[0] <= self._limitmemory:
                texts = []
                while not self._log_message_queue.empty():
                    texts += [self._log_message_queue.get()]
                self._append_to_message_log('\n' + '\n'.join(texts))
            else:
                if not self._maxmemmsg:
                    self._maxmemmsg = '\n' + "Messages log exceeded 80% of " \
                                      "process memory, stopping for now..."
                    self._append_to_message_log(self._maxmemmsg, "stderr")
        if not self._test_runner.is_running():
            self.OnProcessEnded(None)
            return
        out_buffer, err_buffer, log_message = \
            self._test_runner.get_output_and_errors(self.get_current_profile())
        if len(out_buffer) > 0:
            self._append_to_console_log(out_buffer, source="stdout")
        if len(err_buffer) > 0:
            if self._get_last_output_char() != "\n":
                # Robot prints partial lines to stdout to make the
                # interactive experience better. It all goes to
                # heck in a handbasket if something shows up on
                # stderr. So, to fix that we'll add a newline if
                # the previous character isn't a newline.
                self._append_to_console_log("\n")
            self._append_to_console_log(err_buffer, source="stderr")

    def _get_last_output_char(self):
        """Return the last character in the output window"""
        pos = self._console_log_ctrl.PositionBefore(
            self._console_log_ctrl.GetLength())
        char = self._console_log_ctrl.GetCharAt(pos)
        return chr(char)

    def _show_notebook_tab(self):
        """Show the Run notebook tab"""
        if not self.panel:
            self._add_tab_to_notebook()
            self._reload_model()
        self.show_tab(self.panel)

    def _append_to_message_log(self, text, source="stdout"):
        self._append_text(self._message_log_ctrl, text, source)

    def _append_to_console_log(self, text, source="stdout", enc=True):
        """Put output to the text control"""
        self._append_text(self._console_log_ctrl, text, source, enc)
        if self._console_log:
            FileWriter.write(self._console_log, [text], "ab", "a")

    def _append_text(self, text_ctrl, text, source="stdout", enc=True):
        if not self.panel or not text_ctrl:
            return
        text_ctrl.update_scroll_width(text)
        # we need this information to decide whether to autoscroll or not
        new_text_start = text_ctrl.GetLength()
        line_count = text_ctrl.GetLineCount()
        last_visible_line = \
            text_ctrl.GetFirstVisibleLine() + text_ctrl.LinesOnScreen() - 1

        text_ctrl.SetReadOnly(False)
        try:
            if enc:
                if IS_WINDOWS:
                    text_ctrl.AppendText(text.encode('mbcs'))
                else:
                    text_ctrl.AppendText(text.encode(encoding['SYSTEM']))
            else:
                text_ctrl.AppendText(text.encode(encoding['OUTPUT']))
        except UnicodeDecodeError as e:
            # I'm not sure why I sometimes get this, and I don't know what I
            # can do other than to ignore it.
            # print(f"DEBUG: Console print UnicodeDecodeError string is {string}")
            text_ctrl.AppendTextRaw(text)  # DEBUG removed bytes
        except UnicodeEncodeError as e:
            # I'm not sure why I sometimes get this, and I don't know what I
            # can do other than to ignore it.
            # print(f"DEBUG: Console print UnicodeEncodeError string is {string}")
            text_ctrl.AppendTextRaw(text.encode(encoding['CONSOLE']))

        new_text_end = text_ctrl.GetLength()

        if wx.VERSION < (4, 1, 0):
            text_ctrl.StartStyling(new_text_start, 0x1f)
        else:
            text_ctrl.StartStyling(new_text_start)
        if source == "stderr":
            text_ctrl.SetStyling(new_text_end - new_text_start, STYLE_STDERR)

        text_ctrl.SetReadOnly(True)
        if last_visible_line >= line_count - 4:
            line_count = text_ctrl.GetLineCount()
            text_ctrl.ScrollToLine(line_count)

    def _get_console_width(self):
        # robot wants to know a fixed size for output, so calculate the
        # width of the window based on average width of a character. A
        # little is subtracted just to make sure there's a little margin
        out_width, _ = self._console_log_ctrl.GetSize()
        char_width = self._console_log_ctrl.GetCharWidth()
        return str(int(out_width / char_width) - 10)

    def _remove_from_notebook(self):
        """Remove the tab for this plugin from the notebook"""
        if self.notebook:
            self.notebook.allow_closing(self.panel)
            self.notebook.delete_tab(self.panel)

    def _build_runner_toolbar(self, parent):
        toolbar = wx.ToolBar(parent, wx.ID_ANY,
                             style=wx.TB_HORIZONTAL | wx.TB_HORZ_TEXT |
                                   wx.TB_NODIVIDER)
        toolbar.AddTool(ID_RUN, "Start", ImageProvider().TOOLBAR_PLAY,
                        wx.NullBitmap, wx.ITEM_NORMAL, shortHelp="Start robot",
                        longHelp="Start running the robot test suite")
        toolbar.AddTool(ID_RUNDEBUG, "Debug", getBugIconBitmap(), wx.NullBitmap,
                        wx.ITEM_NORMAL, shortHelp="Start robot",
                        longHelp="Start running the robot test suite "
                                 "with DEBUG loglevel")
        toolbar.AddTool(ID_STOP, "Stop", ImageProvider().TOOLBAR_STOP,
                        wx.NullBitmap, wx.ITEM_NORMAL,
                        shortHelp="Stop a running test",
                        longHelp="Stop a running test")
        toolbar.AddTool(ID_PAUSE, "Pause", ImageProvider().TOOLBAR_PAUSE,
                        wx.NullBitmap, wx.ITEM_NORMAL,
                        shortHelp="Pause test execution",
                        longHelp="Pause test execution")
        toolbar.AddTool(ID_CONTINUE, "Continue",
                        ImageProvider().TOOLBAR_CONTINUE,
                        wx.NullBitmap, wx.ITEM_NORMAL,
                        shortHelp="Continue test execution",
                        longHelp="Continue test execution")
        toolbar.AddTool(ID_STEP_NEXT, "Next", ImageProvider().TOOLBAR_NEXT,
                        wx.NullBitmap, wx.ITEM_NORMAL, shortHelp="Step next",
                        longHelp="Step next")
        toolbar.AddTool(ID_STEP_OVER, "Step over", ImageProvider().TOOLBAR_NEXT,
                        wx.NullBitmap, wx.ITEM_NORMAL, shortHelp="Step over",
                        longHelp="Step over")
        toolbar.Realize()
        self._bind_runner_toolbar_events(toolbar)
        return toolbar

    def _bind_runner_toolbar_events(self, toolbar):
        for event, callback, id in (
                (wx.EVT_TOOL, self.OnRun, ID_RUN),
                (wx.EVT_TOOL, self.OnRunDebug, ID_RUNDEBUG),
                (wx.EVT_TOOL, self.OnStop, ID_STOP),
                (wx.EVT_TOOL, self.OnPause, ID_PAUSE),
                (wx.EVT_TOOL, self.OnContinue, ID_CONTINUE),
                (wx.EVT_TOOL, self.OnStepNext, ID_STEP_NEXT),
                (wx.EVT_TOOL, self.OnStepOver, ID_STEP_OVER)):
            toolbar.Bind(event, callback, id=id)

    def _build_local_toolbar(self, parent):
        toolbar = wx.ToolBar(parent, wx.ID_ANY,
                             style=wx.TB_HORIZONTAL | wx.TB_HORZ_TEXT |
                                   wx.TB_NODIVIDER)
        profile_label = Label(toolbar, label="Execution Profile:  ")
        choices = self._test_runner.get_profile_names()
        self.choice = wx.Choice(toolbar, wx.ID_ANY, choices=choices)
        self.choice.SetToolTip(wx.ToolTip("Choose which method to use for "
                                          "running the tests"))
        toolbar.AddControl(profile_label)
        toolbar.AddControl(self.choice)
        toolbar.AddSeparator()
        report_image = getReportIconBitmap()
        log_image = getLogIconBitmap()
        toolbar.AddTool(ID_OPEN_LOGS_DIR, "Open Logs Directory",
                        ImageProvider().DATADIRIMG,
                        shortHelp="View All Logs in Explorer")
        toolbar.AddTool(ID_SHOW_REPORT, " Report", report_image,
                        shortHelp=localize_shortcuts("View Robot Report in "
                                                     "Browser (CtrlCmd-R)"))
        toolbar.AddTool(ID_SHOW_LOG, " Log", log_image,
                        shortHelp=localize_shortcuts("View Robot Log in"
                                                     " Browser (CtrlCmd-L)"))
        toolbar.AddSeparator()
        # the toolbar API doesn't give us a way to specify padding which
        # is why the label has a couple spaces after the colon. gross,
        # but effective.
        self.autosave_cb = \
            self._create_check_box(toolbar, ID_AUTOSAVE, " Autosave  ",
                                   self.auto_save, "Automatically save all "
                                                   "changes before running")
        toolbar.AddControl(self.autosave_cb)

        self.pause_on_failure_cb = \
            self._create_check_box(toolbar, ID_PAUSE_ON_FAILURE,
                                   " Pause after failure  ", False,
                                   "Automatically pause after failing keyword")
        toolbar.AddControl(self.pause_on_failure_cb)

        toolbar.EnableTool(ID_OPEN_LOGS_DIR, False)
        toolbar.EnableTool(ID_SHOW_LOG, False)
        toolbar.EnableTool(ID_SHOW_REPORT, False)
        toolbar.Realize()
        self._bind_local_toolbar_events(toolbar)
        return toolbar

    def _bind_local_toolbar_events(self, toolbar):
        for event, callback, id in (
                (wx.EVT_TOOL, self.OnOpenLogsDirectory, ID_OPEN_LOGS_DIR),
                (wx.EVT_TOOL, self.OnShowReport, ID_SHOW_REPORT),
                (wx.EVT_TOOL, self.OnShowLog, ID_SHOW_LOG)):
            toolbar.Bind(event, callback, id=id)

        for event, handler, source in (
                (wx.EVT_CHECKBOX, self._on_autosave_cb,
                 self.autosave_cb),
                (wx.EVT_CHECKBOX, self._on_pause_on_failure_cb,
                 self.pause_on_failure_cb),
                (wx.EVT_CHOICE, self._on_profile_selection, self.choice)):
            toolbar.Bind(event, handler, source)

    def _on_autosave_cb(self, evt):
        """Called when the user clicks on the "Auto Save" checkbox"""
        self.save_setting("auto_save", evt.IsChecked())

    def _on_pause_on_failure_cb(self, evt):
        self._pause_on_failure = evt.IsChecked()
        self._test_runner.send_pause_on_failure(evt.IsChecked())

    def _on_profile_selection(self, event):
        self.save_setting("profile_name", event.GetString())
        self._set_profile(self.profile_name)

    def _init_profile_choice(self, profile_name):
        """First installation of the profile to be used to run tests"""
        items = self.choice.GetItems()
        if profile_name not in items:
            return
        choice_index = items.index(profile_name)
        self.choice.Select(choice_index)
        self._set_profile(profile_name)

    def _set_profile(self, profile_name):
        """Set the profile to be used to run tests"""
        profile = self._test_runner.get_profile(profile_name)
        self._profile_toolbar = profile.get_toolbar(self._config_panel)

        if self._profile_toolbar:
            sizer = self._config_panel.GetSizer()
            sizer.ShowItems(False)
            sizer.Clear()
            sizer.Add(self._profile_toolbar, 0, wx.EXPAND)
            sizer.ShowItems(True)
            self._config_panel.Parent.Layout()

    def get_current_profile(self):
        return self._test_runner.get_profile(self.choice.GetStringSelection())

    def _add_tab_to_notebook(self):
        self.panel = wx.Panel(self.notebook)
        self._local_toolbar = self._build_local_toolbar(self.panel)
        self._runner_toolbar = self._build_runner_toolbar(self.panel)
        self._config_panel = self._build_config_panel(self.panel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._local_toolbar, 0,
                  wx.EXPAND | wx.LEFT | wx.TOP | wx.RIGHT, 5)
        sizer.Add(wx.StaticLine(self.panel), 0,
                  wx.EXPAND | wx.BOTTOM | wx.TOP, 7)
        sizer.Add(self._runner_toolbar, 0,
                  wx.EXPAND | wx.ALL, 5)
        sizer.Add(wx.StaticLine(self.panel), 0,
                  wx.EXPAND | wx.BOTTOM | wx.TOP, 4)
        sizer.Add(self._config_panel, 0, wx.EXPAND, 5)
        sizer.Add(wx.StaticLine(self.panel), 0,
                  wx.EXPAND | wx.BOTTOM | wx.TOP, 4)
        self._output_panel = self._build_output_panel(self.panel)
        sizer.Add(self._output_panel, 1, wx.EXPAND | wx.TOP, 5)
        self.panel.SetSizer(sizer)

        self._process_timer = wx.Timer(self.panel)
        self.panel.Bind(wx.EVT_TIMER, self.OnTimer)
        self.panel.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

        self.add_tab(self.panel, self.title, allow_closing=False)

    @staticmethod
    def _build_config_panel(parent):
        """Builds the configuration panel for this plugin"""
        panel = wx.Panel(parent, wx.ID_ANY,
                         style=wx.BORDER_NONE | wx.TAB_TRAVERSAL)
        vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(vertical_sizer)
        return panel

    def _build_output_panel(self, parent):
        panel = wx.Panel(parent)
        self._progress_bar = ProgressBar(panel)
        self._console_log_panel, self._console_log_ctrl = \
            self._create_collapsible_pane(panel, 'Console log',
                                          self.show_console_log,
                                          self.OnConsoleLogPaneChanged)
        self._message_log_panel, self._message_log_ctrl = \
            self._create_collapsible_pane(panel, 'Message log',
                                          self.show_message_log,
                                          self.OnMessageLogPaneChanged)

        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(self._progress_bar, 0, wx.EXPAND)
        panel_sizer.Add(self._console_log_panel,
                        int(self.show_console_log),
                        wx.EXPAND)
        panel_sizer.Add(self._message_log_panel,
                        int(self.show_message_log),
                        wx.EXPAND)
        panel.SetSizer(panel_sizer)
        return panel

    def OnConsoleLogPaneChanged(self, evt):
        self.save_setting("show_console_log", not evt.Collapsed)
        self._change_item_proportion(self._output_panel,
                                     self._console_log_panel,
                                     int(not evt.Collapsed))
        self._output_panel.Layout()

    def OnMessageLogPaneChanged(self, evt):
        self.save_setting("show_message_log", not evt.Collapsed)
        self._change_item_proportion(self._output_panel,
                                     self._message_log_panel,
                                     int(not evt.Collapsed))
        self._output_panel.Layout()

    @staticmethod
    def _change_item_proportion(panel, item, proportion):
        sizer = panel.GetSizer()
        children = sizer.GetChildren()
        for itemIndex in range(len(children)):
            if item == children[itemIndex].Window:
                sizer.Detach(item)
                sizer.Insert(itemIndex, item, proportion, wx.EXPAND)
                return

    def _create_collapsible_pane(self, parent, title, expand,
                                 pane_changed_handler):
        collapsible_pane = wx.CollapsiblePane(
            parent, wx.ID_ANY, title,
            style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        if expand:
            collapsible_pane.Expand()
        collapsible_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
                              pane_changed_handler,
                              collapsible_pane)

        pane = collapsible_pane.GetPane()
        text_ctrl = self._create_text_ctrl(pane)

        vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        vertical_sizer.Add(text_ctrl, 1, wx.EXPAND)
        pane.SetSizer(vertical_sizer)
        return collapsible_pane, text_ctrl

    def _create_text_ctrl(self, parent):
        text_ctrl = OutputStyledTextCtrl(parent)
        text_ctrl.SetScrollWidth(100)
        self._set_margins(text_ctrl)
        text_ctrl.SetReadOnly(True)
        return text_ctrl

    @staticmethod
    def _create_check_box(parent, id, label, value, tooltip):
        cb = wx.CheckBox(parent, id, label)
        cb.SetToolTip(wx.ToolTip(tooltip))
        cb.SetValue(value)
        return cb

    @staticmethod
    def _set_margins(out):
        out.SetMarginLeft(10)
        out.SetMarginWidth(0, 0)
        out.SetMarginWidth(1, 0)
        out.SetMarginWidth(2, 0)
        out.SetMarginWidth(3, 0)

    def _test_runner_events_handler(self, event, *args):
        """Endpoint of the listener interface

        This is called via the listener interface. It has an event such as
        "start_suite", "start_test", etc, along with metadata about the event.
         We use this data to update
        the tree and statusbar."""
        if not self.panel:
            # this should only happen if the notebook tab got deleted
            # out from under us. In the immortal words of Jar Jar
            # Binks, "How rude!"
            return
        if event == 'start_test':
            self._handle_start_test(args)
            return
        if event == 'end_test':
            self._handle_end_test(args)
            return
        if event == 'report_file':
            self._handle_report_file(args)
            return
        if event == 'log_file':
            self._handle_log_file(args)
            return
        if event == 'start_keyword':
            self._handle_start_keyword(args)
            return
        if event == 'end_keyword':
            self._handle_end_keyword()
            return
        if event == 'log_message':
            self._handle_log_message(args)
            return
        if event == 'paused':
            self._handle_paused(args)
            return
        if event == 'continue':
            self._handle_continue(args)

    def _handle_start_test(self, args):
        longname = args[1]['longname'].encode('utf-8')
        self._log_message_queue.put(
            f"Starting test: {longname.decode(encoding['OUTPUT'], 'backslashreplace')}")

    def _handle_end_test(self, args):
        longname = args[1]['longname'].encode('utf-8')
        self._log_message_queue.put(
            f"Ending test: {longname.decode(encoding['OUTPUT'], 'backslashreplace')}\n")
        if args[1]['status'] == 'PASS':
            self._progress_bar.add_pass()
        else:
            self._progress_bar.add_fail()

    def _handle_report_file(self, args):
        self._report_file = args[0]
        wx.CallAfter(self._local_toolbar.EnableTool, ID_SHOW_REPORT, True)

    def _handle_log_file(self, args):
        self._log_file = args[0]
        wx.CallAfter(self._local_toolbar.EnableTool, ID_SHOW_LOG, True)

    def _handle_start_keyword(self, args):
        self._progress_bar.set_current_keyword(args[0])

    def _handle_end_keyword(self):
        self._progress_bar.empty_current_keyword()

    def _handle_log_message(self, args):
        a = args[0]
        if LOG_LEVELS[a['level']] >= self._min_log_level_number:
            prefix = '%s : %s : ' % (a['timestamp'], a['level'].rjust(5))
            message = a['message']
            if '\n' in message:
                message = '\n' + message
            self._log_message_queue.put(prefix + message)

    def _handle_paused(self, args):
        wx.CallAfter(self._set_paused)
        self._log_message_queue.put('<<  PAUSED  >>')

    def _handle_continue(self, args):
        wx.CallAfter(self._set_continue)
        self._log_message_queue.put('<< CONTINUE >>')

    def _set_running(self):
        self._run_action.disable()
        self._stop_action.enable()
        self._enable_runner_toolbar(False, True)
        self.get_current_profile().disable_toolbar()
        self._running = True
        self._test_runner.test_execution_started()

    def _set_paused(self):
        self._run_action.disable()
        self._stop_action.enable()
        self._enable_runner_toolbar(False, False)

    def _set_continue(self):
        self._run_action.disable()
        self._stop_action.enable()
        self._enable_runner_toolbar(False, True)

    def _set_stopped(self):
        self._run_action.enable()
        self._stop_action.disable()
        self._enable_runner_toolbar(True, False)
        self.get_current_profile().enable_toolbar()
        self._running = False

    def _enable_runner_toolbar(self, run, paused):
        stop = not run
        debug = stop and not paused
        for id, enabled in ((ID_RUN, run),
                            (ID_RUNDEBUG, run),
                            (ID_STOP, stop),
                            (ID_PAUSE, paused),
                            (ID_CONTINUE, debug),
                            (ID_STEP_NEXT, debug),
                            (ID_STEP_OVER, debug)):
            self._runner_toolbar.EnableTool(id, enabled)

    @staticmethod
    def _notify_user_no_logs_directory():
        wx.MessageBox("There isn't logs directory. \n"
                      "Please, run the tests and try again",
                      "No logs directory",
                      wx.ICON_INFORMATION | wx.OK)


class ProgressBar(wx.Panel):
    """A progress bar for the test runner plugin"""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._gauge = wx.Gauge(self, size=(100, 10))
        self._label = Label(self)
        self._sizer.Add(self._label, 1, wx.EXPAND | wx.LEFT, 10)
        self._sizer.Add(self._gauge, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self._sizer.Layout()
        self.SetSizer(self._sizer)
        self._gauge.Hide()
        self._default_colour = parent.GetBackgroundColour()
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self._initialize_state()

    def _initialize_state(self):
        self._pass = 0
        self._fail = 0
        self._current_keywords = []

    def set_current_keyword(self, name):
        self._current_keywords.append(name)

    def empty_current_keyword(self):
        if self._current_keywords:
            self._current_keywords.pop()

    def OnTimer(self, event):
        """A handler for timer events; it updates the statusbar"""
        self._gauge.Show()
        self._gauge.Pulse()
        self._update_message()

    def Start(self):
        """Signals the start of a test run; initialize progressbar."""
        self._initialize_state()
        self._start_time = time.time()
        self._gauge.Show()
        self._sizer.Layout()
        self.SetBackgroundColour(self._default_colour)
        self._timer.Start(50)

    def Stop(self):
        """Signals the end of a test run"""
        self._gauge.Hide()
        self._timer.Stop()

    def add_pass(self):
        """Add one to the passed count"""
        self._pass += 1

    def add_fail(self):
        """Add one to the failed count"""
        self._fail += 1

    def _update_message(self):
        """Update the displayed elapsed time, passed and failed counts"""
        elapsed = time.time() - self._start_time
        message = "elapsed time: %s     pass: %s     fail: %s" % (
            self._seconds_to_string(elapsed), self._pass, self._fail)
        message += self._get_current_keyword_text()
        self._label.SetLabel(message)
        if self._fail > 0:
            self.SetBackgroundColour("#FF8E8E")
        elif self._pass > 0:
            self.SetBackgroundColour("#9FCC9F")
        # not sure why this is required, but without it the background
        # colors don't look right on Windows
        self.Refresh()

    def _get_current_keyword_text(self):
        if not self._current_keywords:
            return ''
        return '     current keyword: ' + \
               self._fix_size(' -> '.join(self._current_keywords), 50)

    @staticmethod
    def _fix_size(text, max_length):
        if len(text) <= max_length:
            return text
        return '...' + text[3 - max_length:]

    # stole this off the internet. Nifty.
    @staticmethod
    def _seconds_to_string(t):
        """Convert a number of seconds to a string of the form HH:MM:SS"""
        return "%d:%02d:%02d" % \
               reduce(lambda ll, b: divmod(ll[0], b) + ll[1:], [(t,), 60, 60])


class OutputStyledTextCtrl(wx.stc.StyledTextCtrl):

    def __init__(self, parent):
        wx.stc.StyledTextCtrl.__init__(self, parent, wx.ID_ANY,
                                       style=wx.SUNKEN_BORDER)
        app_settings = self._get_app_settings(parent)
        self.stylizer = OutputStylizer(self, app_settings)
        self._max_row_len = 0

    def update_scroll_width(self, string):
        string_max_len = max(len(s) for s in string.split('\n'))
        if string_max_len <= self._max_row_len:
            return
        self._max_row_len = string_max_len
        try:
            width, _ = self.GetTextExtent(string)
            if self.GetScrollWidth() < width + 50:
                self.SetScrollWidth(width + 50)
        except UnicodeDecodeError:
            pass

    @staticmethod
    def _get_app_settings(parent):
        while True:
            if not parent:
                raise ValueError('Value does not contain NoteBook as parent')
            if isinstance(parent, NoteBook):
                return parent._app.settings
            parent = parent.GetParent()


class OutputStylizer(object):
    def __init__(self, editor, settings):
        self.editor = editor
        self.settings = settings._config_obj['Plugins']['Test Runner']
        self._ensure_default_font_is_valid()
        self._set_styles()
        PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)

    def OnSettingsChanged(self, message):
        """Redraw colors and font if settings are modified"""
        section, setting = message.keys
        if section == 'Test Runner':
            self._set_styles()

    def _set_styles(self):
        """Sets plugin styles"""
        background = self.settings.get('background', 'white')
        font_size = self.settings.get('font size', 10)
        font_face = self.settings.get('font face', 'Courier New')

        default_style = self._get_style_string(
            fore=self.settings.get('foreground', 'black'), back=background,
            size=font_size, face=font_face)
        error_style = self._get_style_string(
            fore=self.settings.get('error', 'red'), back=background,
            size=font_size, face=font_face)

        self.editor.StyleSetSpec(STYLE_DEFAULT, default_style)
        self.editor.StyleSetSpec(STYLE_STDERR, error_style)
        self.editor.StyleSetSpec(7, error_style)
        self.editor.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, background)
        self.editor.Refresh()

    @staticmethod
    def _get_style_string(back, fore, size, face):
        return ','.join('%s:%s' % (name, value)
                        for name, value in locals().items() if value)

    def _ensure_default_font_is_valid(self):
        """Checks if default font is installed"""
        default_font = self.settings.get('font face')
        if default_font not in ReadFonts():
            sys_font = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT)
            self.settings['font face'] = sys_font.GetFaceName()


Robot = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAnNJ"
    "REFUOI2Vkb1Pk3EQxz/PW6EvUN6sEQFBIwUlMBgTMZFZJzcXEzeJiXE1MXFi4g8gGhjcHDA4"
    "iFGDKNFojBoJaqQItgrlpYUW0ZZSaJ/ndw5INQZIvMttd5/73vcQEbYrpRSPes5K7NsrUaK2"
    "7RERdHaJnLeV4tL9u7XsDNA0qKhrw19erf0nQABBRBEeGyT86YUgIKjtF4nIP+PC0tsRGb11"
    "g+hcnAqvl6ZjrQQ7r664ygIV/8opAATIpr53fui53psZfoqsZcn5TEyXjlrPQcNBvMdO0XG5"
    "S4M/GPNvWnQ23Ptg4hW1xxsxLAssE0MHHIWgM/f+Me35a1iWmy1IASCOw+f+XhwMQuML/Eik"
    "WVA6mlLU6A7+AwEqKxSjN7vlxJUubUtEwcTJ8XF5PfAA23ZIJTMkppdoathLS7CO5EyS1M8M"
    "GjpDdwcR/vhWUHAo2KjtaWmWeWeJtlNH0DqamPwSxTQtTl88g21nWUlG6bhwficThWQsKpfO"
    "tWMkBFGQXc9j6RYuw8F0WXgOe+i7F9LQTLZu0Au/V8Lzh32UFBfjK3dRWlVEoMaDf59JSbUH"
    "d5ULv7uI+7e7RZT9+2+gC5sZ/Tom4U/P8PgMViVHWjZYNxxsl7Bh2uDTCFT7+Dw2ROjdw9/C"
    "BfN7fEp+LLxkMrxIKp0mGDxAc8s6dXvrQRc0TUfTYSocxs7rxBOrfHxzh3J/Tvz7TmImYhMs"
    "Rl4zG1lDicOT4RBHWyr5GBrH0DcvdGxFWUme+Zk0tY2lzM3NshyfxHDXo0fCEQb6R4hMx3Bs"
    "hTiCKMFtpsmoLHl7Ga8fRATHEcRRrCxnGBocIR6L8Qu2hlAKJu0L3QAAAABJRU5ErkJggg==")
getRobotBitmap = Robot.GetBitmap

MenuButton = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAKxJ"
    "REFUOI3t0jEKg0AUBNAxhmXX9QD2adLnJt7E2luIeB/PkCoQCG5lK8ifdZtNHyQRLGwy5Yd5"
    "/GKSGCP25LSr/QcAAOfPQ9/3MYSAZVngvQdJiAhEhFVVZT8BkpKmaZbnOZRS0FojhIBpmh6b"
    "Ppjn+ULyqZSyxhiM44hhGEiyXAOStSG1bVuIyMtaq51zJHltmsZtBgCgruuC5N17f+u6brX8"
    "Fdia43dwPPAGncZYbvceeuMAAAAASUVORK5CYII=")
getMenuButtonBitmap = MenuButton.GetBitmap

ProcessStop = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdBTUEAAK/INwWK6QAAABl0"
    "RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAJJSURBVDjLpZNNbxJRFIb7A/wF"
    "/A5YunRDovsmRk3cmLAxcdG0uiFuXDSmkBlLFNOmtYFKgibUtqlJG6UjiGksU0oZPgQs0KEw"
    "Mw4Dw8dQjnPuMCNq48abvJub87zn4547BQBTk7q2CDZdDl1OXdNjOcd3tj/jJ8Eruuxzb2RX"
    "+NMpHT/MMUfHJwKbSgv7Bxnm9YciPRMSXRiDsb8ZjOGrwWjNzZ4UOL4pg6IOQLsYEbU6fajW"
    "RYgdpLilnYIbY00T08COcCrzTen2NMCj9ocgKgMQdLV7Q3KnqH3YTyQV/1YWTezEAPvCsjGz"
    "CTfkPtR/9IGXDNWkHlTFnmWysxfj7q/x2I4NDRxh5juNZf8LPm12ifBkimdAheI0smjgjH3N"
    "MtgzlmqCNx5tGnq4Abe9LIHLjS7IHQ3OJRWW1zcYZNFgOnl0LOCwmq0BgTEjgqbQoHSuQrGu"
    "EqO+dgFrgXUBWWJwyKaIAZaPcEXoWvD1uQjc8rBQ4FUio4oBLK+8sgycH7+kGUnpQUvVrF4x"
    "K4KomwuGQf6sQ14mV5GA8gesFhyB3TxdrjZhNAKSwSzXzIpgrtaBbLUDg+EI9j6nwe3btIZo"
    "exBsuHajCU6QjSlfBmaqbZIgr2f3Pl/l7vpyxjOai0S9Zd2R91GFF41Aqa1Z1eAyYeZcRQSP"
    "P6jMUlu/FmlylecDCfdqKMLFk3ko8zKZCfacLgmwHWVhnlriZrzv/l7lyc9072XJ9fjFNv10"
    "cYWhnvmEBS8tPPH4mVlPmL5DZy7/TP/znX8C6zgR9sd1gukAAAAASUVORK5CYII=")
getProcessStopBitmap = ProcessStop.GetBitmap

# page_white.png from http://www.famfamfam.com/lab/icons/silk
ReportIcon = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAQAAAC1+jfqAAAABGdBTUEAAK/INwWK6QAAABl0"
    "RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAC4SURBVCjPdZFbDsIgEEWnrsMm"
    "7oGGfZrohxvU+Iq1TyjU60Bf1pac4Yc5YS4ZAtGWBMk/drQBOVwJlZrWYkLhsB8UV9K0BUrP"
    "Gy9cWbng2CtEEUmLGppPjRwpbixUKHBiZRS0p+ZGhvs4irNEvWD8heHpbsyDXznPhYFOyTjJ"
    "c13olIqzZCHBouE0FRMUjA+s1gTjaRgVFpqRwC8mfoXPPEVPS7LbRaJL2y7bOifRCTEli3U7"
    "BMWgLzKlW/CuebZPAAAAAElFTkSuQmCC")
getReportIconBitmap = ReportIcon.GetBitmap

# page_white_text.png from http://www.famfamfam.com/lab/icons/silk
LogIcon = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAQAAAC1+jfqAAAABGdBTUEAAK/INwWK6QAAABl0"
    "RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAADoSURBVBgZBcExblNBGAbA2cee"
    "gTRBuIKOgiihSZNTcC5LUHAihNJR0kGKCDcYJY6D3/77MdOinTvzAgCw8ysThIvn/VojIyMj"
    "IyPP+bS1sUQIV2s95pBDDvmbP/mdkft83tpYguZq5Jh/OeaYh+yzy8hTHvNlaxNNczm+la9O"
    "Tlar1UdA/+C2A4trRCnD3jS8BB1obq2Gk6GU6QbQAS4BUaYSQAf4bhhKKTFdAzrAOwAxEUAH"
    "+KEM01SY3gM6wBsEAQB0gJ+maZoC3gI6iPYaAIBJsiRmHU0AALOeFC3aK2cWAACUXe7+AwO0"
    "lc9eTHYTAAAAAElFTkSuQmCC")
getLogIconBitmap = LogIcon.GetBitmap

# bug.png from http://www.famfamfam.com/lab/icons/silk
BugIcon = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdBTUEAAK/INwWK6QAAABl0"
    "RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAKYSURBVDjLnZPJT1NRFMb5G1wD"
    "HV5boNiqdHrvFYolCAtsGSSWKpMFKhYqlDI6oAEKaVJwCIgSphaKtLYWCgSNBgRjMNHoxsSF"
    "S3cmJmA0NMTw+R6JKKZl4eJL7sm953fOd3JPHIC4WMpcppG5SGnZc8ZjVVF6QLn975sDgfaZ"
    "mvg71oRJZIRUYcuAnq/2KWroGfm3QwEn2YpLVPPvOD2oiqj9yq/mGznegl56mx6T7ZbY1M6Y"
    "AM0CuZkxT0b2Wg6QW/SsApRXDsotR+d6E9Y/h9DuqoCuJq0lKoDxqU1/pITGR27mBU4h+GEc"
    "Tz5OY+ClA5JbyahYzof/9TBO9B/FcWcqpA4xU3We3GJ87ntnfO5meinMvruNnqcmXA2XoDVc"
    "Cc0wCYkzBaZpA7ILRJ/2O2B87jA+QT9UeDRe8svZYAG8b/txc6kc9mA+yqayYPQXwvdmBEOr"
    "A5B2p0BtFIYOWKCm5RukWwZyXIbA+0F0LpaiKaBHmVsLw4we99ccsM8a8GClF5JOMcQdou8p"
    "rULrgRmQo7KI0VcE13MrGv06lE5kodhzGvdWu2GdKkTVWC4DcELcJkKyXbCb1EhAVM//M0DV"
    "UNqP2qAJd1baUDaZjTMTeXAttsPi0cM0mgvHvA0NkxYk2QRIrieOsDmEmXttH0DfVfSluSTo"
    "WmpD8bgOroUOWNw6VI7koGfOBuq6EqLLTNU6ojrmP5D1HVsjmrkYezGIrlA9LjKgnrlGXJlp"
    "gbCOD0EtD0QNN8I3cZqjAlhJr4rXpB1iNLhrYffUQWoT7yUKzbxqJlHLq0jc5JYmgHMunogK"
    "YJVqF7mTrPyfgktMRTMX/CrOq1gLF3fYNrLiX+Bs8MoTwT2fQPwXgBXHGL+TaIjfinb3C7cs"
    "cRMIcYL6AAAAAElFTkSuQmCC")
getBugIconBitmap = BugIcon.GetBitmap
