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
import datetime
import time
import os
import re
import wx
import wx.stc
from functools import reduce
try:
    from Queue import Queue
except ImportError: # Python 3
    from queue import Queue
from wx.lib.embeddedimage import PyEmbeddedImage


from robotide.action.shortcut import localize_shortcuts
from robotide.context import IS_WINDOWS, IS_MAC
from robotide.contrib.testrunner import TestRunner
from robotide.contrib.testrunner import runprofiles
from robotide.publish import RideSettingsChanged, PUBLISHER
from robotide.publish.messages import RideTestSelectedForRunningChanged
from robotide.pluginapi import Plugin, ActionInfo
from robotide.widgets import Label, ImageProvider
from robotide.robotapi import LOG_LEVELS
from robotide.utils import robottime, is_unicode, PY2
from robotide.preferences.editors import ReadFonts
from sys import getfilesystemencoding
from robotide.lib.robot.utils.encodingsniffer import (get_console_encoding,
                                                      get_system_encoding)
CONSOLE_ENCODING = get_console_encoding()
if PY2 and IS_WINDOWS:
    SYSTEM_ENCODING = 'mbcs'
else:
    SYSTEM_ENCODING = get_system_encoding()
OUTPUT_ENCODING = getfilesystemencoding()
encoding = {'CONSOLE': CONSOLE_ENCODING,
            'SYSTEM': SYSTEM_ENCODING,
            'OUTPUT': OUTPUT_ENCODING}

# print("DEBUG: TestRunnerPlugin encoding=%s" % encoding)

ID_RUN = wx.NewId()
ID_RUNDEBUG = wx.NewId()
ID_STOP = wx.NewId()
ID_PAUSE = wx.NewId()
ID_CONTINUE = wx.NewId()
ID_STEP_NEXT = wx.NewId()
ID_STEP_OVER = wx.NewId()
ID_SHOW_REPORT = wx.NewId()
ID_SHOW_LOG = wx.NewId()
ID_AUTOSAVE = wx.NewId()
ID_PAUSE_ON_FAILURE = wx.NewId()
ID_SHOW_MESSAGE_LOG = wx.NewId()
STYLE_DEFAULT = 0
STYLE_STDERR = 2


def _RunProfile(name, run_prefix):
    return type('Profile', (runprofiles.PybotProfile,),
                {'name': name, 'get_command': lambda self: run_prefix})


class TestRunnerPlugin(Plugin):
    """A plugin for running tests from within RIDE"""
    defaults = {"auto_save": False,
                "show_message_log": True,
                "confirm run": True,
                "profile": "robot",
                "sash_position": 200,
                "runprofiles":
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
        self.version = "3.01"
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
        self._names_to_run = set()

    def _register_shortcuts(self):
        self.register_shortcut('CtrlCmd-C', self._copy_from_out)
        self.register_shortcut('CtrlCmd-L', self.OnShowLog)
        self.register_shortcut('CtrlCmd-R', self.OnShowReport)
        if IS_WINDOWS or IS_MAC:
            self.register_shortcut('Del', self._delete_pressed)

    def _delete_pressed(self, event):
        if self.notebook.current_page_title != self.title:
            return
        self.get_current_profile().delete_pressed()

    def _copy_from_out(self, event):
        if self.notebook.current_page_title != self.title:
            return
        if self.out.GetSTCFocus():
            self.out.Copy()
            return
        if self.message_log.GetSTCFocus():
            self.message_log.Copy()
            return

    def enable(self):
        self.tree.set_checkboxes_for_tests()
        self._read_run_profiles()
        self._register_actions()
        self._build_ui()
        self.SetProfile(self.profile)
        self._subscribe_to_events()
        self._test_runner.enable(self._post_result)
        self._set_stopped()

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
                                             self.runprofiles]

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

    def OnSettingsChanged(self, data):
        '''Updates settings'''
        section, setting = data.keys
        # print("DEBUG: enter OnSettingsChanged section %s" % (section))
        if section == 'Test Run':  # DEBUG temporarily we have two sections
            # print("DEBUG: setting.get('confirm run')= %s " % setting)
            # print("DEBUG: new data= %s old %s new %s" % (data.keys, data.old, data.new))
            self.defaults.setdefault(setting, data.new)
            self.save_setting(setting, data.new)

    def OnTestSelectedForRunningChanged(self, message):
        self._names_to_run = message.tests

    def disable(self):
        self._remove_from_notebook()
        self._test_runner.clear_server()
        self.unsubscribe_all()
        self.unregister_actions()

    def OnClose(self, event):
        """Shut down the running services and processes"""
        self._test_runner.kill_process()
        if self._process_timer:
            self._process_timer.Stop()
        self._test_runner.shutdown_server()
        event.Skip()

    def OnAutoSaveCheckbox(self, evt):
        """Called when the user clicks on the "Auto Save" checkbox"""
        self.save_setting("auto_save", evt.IsChecked())

    def OnShowHideMessageLog(self, evt):
        checked = evt.IsChecked()
        self.save_setting("show_message_log", checked)
        if checked:
            self._show_message_log()
        else:
            self._hide_message_log()

    def OnPauseOnFailureCheckbox(self, evt):
        self._test_runner.set_pause_on_failure(evt.IsChecked())

    def _show_message_log(self):
        self.message_log = self._create_output_textctrl()
        self._right_panel.GetSizer().Add(self.message_log, 1, wx.EXPAND)
        self._right_panel.GetSizer().Layout()

    def _hide_message_log(self):
        self._clear_text(self.message_log)
        self._right_panel.RemoveChild(self.message_log)
        self.message_log.Destroy()
        self.message_log = None
        self._right_panel.GetSizer().Layout()

    def OnStop(self, event):
        """Called when the user clicks the "Stop" button

        This sends a SIGINT to the running process, with the
        same effect as typing control-c when running from the
        command line."""
        self._AppendText(self.out, '[ SENDING STOP SIGNAL ]\n',
                         source='stderr')
        self._test_runner.send_stop_signal()

    def OnPause(self, event):
        self._AppendText(self.out, '[ SENDING PAUSE SIGNAL ]\n')
        self._test_runner.send_pause_signal()

    def OnContinue(self, event):
        self._AppendText(self.out, '[ SENDING CONTINUE SIGNAL ]\n')
        self._test_runner.send_continue_signal()

    def OnStepNext(self, event):
        self._AppendText(self.out, '[ SENDING STEP NEXT SIGNAL ]\n')
        self._test_runner.send_step_next_signal()

    def OnStepOver(self, event):
        self._AppendText(self.out, '[ SENDING STEP OVER SIGNAL ]\n')
        self._test_runner.send_step_over_signal()

    def OnRunDebug(self, event):
        """ Called when the user clicks or presses the F9, Run with Debug
            It can still be overwritten in RIDE Arguments line
        """
        # Save the original function so we can inject "-L Debug"
        tempFunc = self._create_command 
        self._create_command = self._create_debug_command
        # Do normal run with
        self.OnRun(event)
        # Restore original function
        self._create_command = tempFunc

    def OnRun(self, event):
        """Called when the user clicks the "Run" button"""
        if not self._can_start_running_tests():
            return
        #if no tests are selected warn the user, issue #1622
        if self.__getattr__('confirm run'):
            if not self.tests_selected():
                if not self.ask_user_to_run_anyway():
                    # In Linux NO runs dialog 4 times
                    return
        self._initialize_ui_for_running()
        command = self._create_command()
        if PY2:
            self._output("command: %s\n" % command)  # DEBUG encode
        else:
            self._output("command: %s\n" % command, enc=False)  # DEBUG on Py3 it not shows correct if tags with latin chars
        try:
            if PY2 and IS_WINDOWS:
                cwd = self._get_current_working_dir()  # DEBUG It fails if a directory has chinese or latin symbols
                cwd = cwd.encode(encoding['OUTPUT']) # DEBUG SYSTEM_ENCODING
                # print("DEBUG: encoded cwd: %s" % cwd)
                self._test_runner.run_command(command.encode(encoding['OUTPUT']), cwd)  # --include Áçãoµ
            else:
                self._test_runner.run_command(command, self._get_current_working_dir())
            # self._output("DEBUG: Passed test_runner.run_command\n")
            self._process_timer.Start(41)  # roughly 24fps
            self._set_running()
            self._progress_bar.Start()
        except Exception as e:
            # self._output("DEBUG: Except block test_runner.run_command\n")
            self._set_stopped()
            error, log_message = self.get_current_profile().format_error(str(e), None)  # DEBUG unicode(e)
            self._output(error)
            if log_message:
                log_message.publish()

    def _create_command(self):
        command_as_list = self._test_runner.get_command(
            self.get_current_profile(),
            self.global_settings.get('pythonpath', None),
            self._get_console_width(),
            self._names_to_run)
        self._min_log_level_number = \
            self._test_runner.get_message_log_level(command_as_list)
        command = self._format_command(command_as_list)
        return command

    def _create_debug_command(self):
        command_as_list = self._test_runner.get_command(
            self.get_current_profile(),
            self.global_settings.get('pythonpath', None),
            self._get_console_width(),
            self._names_to_run)
        if '-L' not in command_as_list:
            command_as_list.insert(1, '-L')
            command_as_list.insert(2, 'DEBUG')
        self._min_log_level_number = self._test_runner.get_message_log_level(
            command_as_list)
        command = self._format_command(command_as_list)
        return command

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

    def _ask_user_to_save_before_running(self):
        ret = wx.MessageBox("""There are unsaved modifications.
        Do you want to save all changes and run the tests?""",
                            "Unsaved Modifications",
                            wx.ICON_QUESTION | wx.YES_NO)
        return ret == wx.YES

    def tests_selected(self):
        return len(self._names_to_run) != 0

    def ask_user_to_run_anyway(self):
        ret = wx.MessageBox('No tests selected. \n'
                            'Continue anyway?',
                            'No tests selected',
                            wx.ICON_QUESTION | wx.YES_NO)
        return ret == wx.YES

    def _initialize_ui_for_running(self):
        self._show_notebook_tab()
        self._clear_output_window()
        self.local_toolbar.EnableTool(ID_SHOW_REPORT, False)
        self.local_toolbar.EnableTool(ID_SHOW_LOG, False)
        self._report_file = self._log_file = None
        self._messages_log_texts = Queue()

    def _clear_output_window(self):
        self._clear_text(self.out)
        if self.message_log:
            self._clear_text(self.message_log)

    def _clear_text(self, textctrl):
        textctrl.SetReadOnly(False)
        textctrl.ClearAll()
        textctrl.SetReadOnly(True)

    def OnShowReport(self, evt):
        """Called when the user clicks on the "Report" button"""
        if self._report_file:
            wx.LaunchDefaultBrowser("file:%s" %
                                    os.path.abspath(self._report_file))

    def OnShowLog(self, evt):
        """Called when the user clicks on the "Log" button"""
        if self._log_file:
            wx.LaunchDefaultBrowser("file:%s" %
                                    os.path.abspath(self._log_file))

    def OnProfileSelection(self, event):
        self.save_setting("profile", event.GetString())
        self.SetProfile(self.profile)

    def OnProcessEnded(self, evt):
        output, errors, log_message = self._test_runner.get_output_and_errors(
            self.get_current_profile())
        self._output(output)
        self._read_report_and_log_from_stdout_if_needed()
        if len(errors) > 0:
            self._output("unexpected error: " + errors)
        if self._process_timer:
            self._process_timer.Stop()
        self._set_stopped()
        self._progress_bar.Stop()
        now = datetime.datetime.now()
        self._output("\ntest finished %s" %
                     robottime.format_time(now.timetuple()))
        self._test_runner.command_ended()
        if log_message:
            log_message.publish()

    def _read_report_and_log_from_stdout_if_needed(self):
        output = self.out.GetText()
        if not self._report_file:
            self._report_file = self._get_report_or_log(output,
                                                        self.report_regex)
            if self._report_file:
                self.local_toolbar.EnableTool(ID_SHOW_REPORT, True)
        if not self._log_file:
            self._log_file = self._get_report_or_log(output, self.log_regex)
            if self._log_file:
                self.local_toolbar.EnableTool(ID_SHOW_LOG, True)

    def _get_report_or_log(self, output, regex):
        res = regex.search(output)
        return res.group(1) if res and os.path.isfile(res.group(1)) else None

    def OnTimer(self, evt):
        """Get process output"""
        if not self._test_runner.is_running():
            self.OnProcessEnded(None)
            return
        out_buffer, err_buffer, log_message =\
            self._test_runner.get_output_and_errors(self.get_current_profile())
        if len(out_buffer) > 0:
            self._output(out_buffer, source="stdout")
        if len(err_buffer) > 0:
            if self.GetLastOutputChar() != "\n":
                # Robot prints partial lines to stdout to make the
                # interactive experience better. It all goes to
                # heck in a handbasket if something shows up on
                # stderr. So, to fix that we'll add a newline if
                # the previous character isn't a newline.
                self._output("\n", source="stdout")
            self._output(err_buffer, source="stderr")
        if self.message_log and not self._messages_log_texts.empty():
            texts = []
            while not self._messages_log_texts.empty():
                texts += [self._messages_log_texts.get()]
            self._AppendText(self.message_log, '\n'+'\n'.join(texts))

    def GetLastOutputChar(self):
        """Return the last character in the output window"""
        pos = self.out.PositionBefore(self.out.GetLength())
        char = self.out.GetCharAt(pos)
        return chr(char)

    def _format_command(self, argv):
        """Quote a list as if it were a command line command

        This isn't perfect but seems to work for the normal use
        cases. I'm not entirely sure what the perfect algorithm
        is since *nix and windows have different quoting
        behaviors.
        """
        result = []
        for arg in argv:
            if PY2 and is_unicode(arg):
                arg = arg.encode(encoding['SYSTEM'])  # DEBUG "utf-8") CONSOLE_ENCODING
                # print("DEBUG: PY2 unicode args %s" % arg)
            if "'" in arg or " " in arg or "&" in arg:
                # for windows, if there are spaces we need to use
                # double quotes. Single quotes cause problems
                result.append('"%s"' % arg)
            elif '"' in arg:
                result.append("'%s'" % arg)
            else:
                result.append(arg)
        return " ".join(result)  # DEBUG added bytes

    def _show_notebook_tab(self):
        """Show the Run notebook tab"""
        if not self.panel:
            self._build_notebook_tab()
            self._reload_model()
        self.show_tab(self.panel)

    def _AppendText(self, textctrl, string, source="stdout", enc=True):
        if not self.panel or not textctrl:
            return
        textctrl.update_scroll_width(string)
        # we need this information to decide whether to autoscroll or not
        new_text_start = textctrl.GetLength()
        linecount = textctrl.GetLineCount()
        lastVisibleLine = textctrl.GetFirstVisibleLine() + \
                          textctrl.LinesOnScreen() - 1

        textctrl.SetReadOnly(False)
        try:
            if enc:
                textctrl.AppendText(string.encode(encoding['SYSTEM']))
            else:
                textctrl.AppendText(string)
            # print("DEBUG _AppendText Printed OK")
        except UnicodeDecodeError as e:
            # I'm not sure why I sometimes get this, and I don't know what I
            # can do other than to ignore it.
            if PY2:
                if is_unicode(string):
                    textctrl.AppendTextRaw(bytes(string.encode('utf-8')))
                else:
                    textctrl.AppendTextRaw(string)
            else:
                textctrl.AppendTextRaw(bytes(string, encoding['SYSTEM']))  # DEBUG .encode('utf-8'))
            # print(r"DEBUG UnicodeDecodeError appendtext string=%s\n" % string)
            pass
        except UnicodeEncodeError as e:
            # I'm not sure why I sometimes get this, and I don't know what I
            # can do other than to ignore it.
            textctrl.AppendText(string.encode('utf-8'))  # DEBUG .encode('utf-8'))
            # print(r"DEBUG UnicodeDecodeError appendtext string=%s\n" % string)
            pass
            #  raise  # DEBUG

        new_text_end = textctrl.GetLength()

        textctrl.StartStyling(new_text_start, 0x1f)
        if source == "stderr":
            textctrl.SetStyling(new_text_end-new_text_start, STYLE_STDERR)

        textctrl.SetReadOnly(True)
        if lastVisibleLine >= linecount-4:
            linecount = textctrl.GetLineCount()
            textctrl.ScrollToLine(linecount)

    def _get_console_width(self):
        # robot wants to know a fixed size for output, so calculate the
        # width of the window based on average width of a character. A
        # little is subtracted just to make sure there's a little margin
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            out_width, _ = self.out.GetSize()
        else:
            out_width, _ = self.out.GetSizeTuple()
        char_width = self.out.GetCharWidth()
        return str(int(out_width/char_width)-10)

    def _build_ui(self):
        """Creates the UI for this plugin"""
        self._build_notebook_tab()

    def _remove_from_notebook(self):
        """Remove the tab for this plugin from the notebook"""
        if self.notebook:
            self.notebook.allow_closing(self.panel)
            self.notebook.delete_tab(self.panel)

    def _build_config_panel(self, parent):
        """Builds the configuration panel for this plugin"""
        panel = wx.Panel(parent, wx.ID_ANY, style=wx.BORDER_NONE |
                                                  wx.TAB_TRAVERSAL)
        self.config_sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(self.config_sizer)
        self.config_panel = panel
        return panel

    def _output(self, string, source="stdout", enc=True):
        """Put output to the text control"""
        self._AppendText(self.out, string, source, enc)

    def _build_runner_toolbar(self):
        toolbar = wx.ToolBar(self.panel, wx.ID_ANY,
                             style=wx.TB_HORIZONTAL | wx.TB_HORZ_TEXT)
        # DEBUG wxPhoenix toolbar.AddLabelTool(
        self.MyAddTool(toolbar, ID_RUN, "Start", ImageProvider().TOOLBAR_PLAY,
                       shortHelp="Start robot",
                       longHelp="Start running the robot test suite")
        self.MyAddTool(toolbar, ID_RUNDEBUG, "Debug", getBugIconBitmap(),
                       shortHelp="Start robot",
                       longHelp="Start running the robot test suite "
                                "with DEBUG loglevel")
        self.MyAddTool(toolbar, ID_STOP, "Stop", ImageProvider().TOOLBAR_STOP,
                       shortHelp="Stop a running test",
                       longHelp="Stop a running test")
        self.MyAddTool(toolbar, ID_PAUSE, "Pause",
                       ImageProvider().TOOLBAR_PAUSE,
                       shortHelp="Pause test execution",
                       longHelp="Pause test execution")
        self.MyAddTool(toolbar, ID_CONTINUE, "Continue",
                       ImageProvider().TOOLBAR_CONTINUE,
                       shortHelp="Continue test execution",
                       longHelp="Continue test execution")
        self.MyAddTool(toolbar, ID_STEP_NEXT, "Next",
                       ImageProvider().TOOLBAR_NEXT,
                       shortHelp="Step next", longHelp="Step next")
        self.MyAddTool(toolbar, ID_STEP_OVER, "Step over",
                       ImageProvider().TOOLBAR_NEXT,
                       shortHelp="Step over", longHelp="Step over")
        toolbar.Realize()
        self._bind_runner_toolbar_events(toolbar)
        return toolbar

    def MyAddTool(self, obj, toolid, label, bitmap, bmpDisabled=wx.NullBitmap,
                  kind=wx.ITEM_NORMAL, shortHelp="", longHelp=""):
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            obj.AddTool(toolid, label, bitmap, bmpDisabled, kind,
                        shortHelp, longHelp)
        else:
            obj.AddLabelTool(toolid, label, bitmap, shortHelp=shortHelp,
                             longHelp=longHelp)

    def _bind_runner_toolbar_events(self, toolbar):
        for event, callback, id in ((wx.EVT_TOOL, self.OnRun, ID_RUN),
                                    (wx.EVT_TOOL, self.OnRunDebug, ID_RUNDEBUG
                                     ),
                                    (wx.EVT_TOOL, self.OnStop, ID_STOP),
                                    (wx.EVT_TOOL, self.OnPause, ID_PAUSE),
                                    (wx.EVT_TOOL, self.OnContinue, ID_CONTINUE
                                     ),
                                    (wx.EVT_TOOL, self.OnStepNext, ID_STEP_NEXT
                                     ),
                                    (wx.EVT_TOOL, self.OnStepOver, ID_STEP_OVER
                                     )):
            toolbar.Bind(event, callback, id=id)

    def _build_local_toolbar(self):
        toolbar = wx.ToolBar(self.panel, wx.ID_ANY,
                             style=wx.TB_HORIZONTAL | wx.TB_HORZ_TEXT)
        profileLabel = Label(toolbar, label="Execution Profile:  ")
        choices = self._test_runner.get_profile_names()
        self.choice = wx.Choice(toolbar, wx.ID_ANY, choices=choices)
        self.choice.SetToolTip(wx.ToolTip("Choose which method to use for "
                                          "running the tests"))
        toolbar.AddControl(profileLabel)
        toolbar.AddControl(self.choice)
        toolbar.AddSeparator()
        reportImage = getReportIconBitmap()
        logImage = getLogIconBitmap()
        # DEBUG wxPhoenix toolbar.AddLabelTool(
        self.MyAddTool(toolbar, ID_SHOW_REPORT, " Report", reportImage,
                       shortHelp=localize_shortcuts("View Robot Report in "
                                                    "Browser (CtrlCmd-R)"))
        self.MyAddTool(toolbar, ID_SHOW_LOG, " Log", logImage,
                       shortHelp=localize_shortcuts("View Robot Log in"
                                                    " Browser (CtrlCmd-L)"))
        toolbar.AddSeparator()
        # the toolbar API doesn't give us a way to specify padding which
        # is why the label has a couple spaces after the colon. gross,
        # but effective.
        self.savecb = wx.CheckBox(toolbar, ID_AUTOSAVE, " Autosave  ")
        self.savecb.SetToolTip(wx.ToolTip("Automatically save all changes "
                                          "before running"))
        self.savecb.SetValue(self.auto_save)
        toolbar.AddControl(self.savecb)

        self.pause_after_failure_cb = wx.CheckBox(toolbar, ID_PAUSE_ON_FAILURE,
                                                  " Pause on failure  ")
        self.pause_after_failure_cb.SetToolTip(wx.ToolTip("Automatically pause"
                                                          " after failing "
                                                          "keyword"))
        self.pause_after_failure_cb.SetValue(False)
        toolbar.AddControl(self.pause_after_failure_cb)

        self.show_log_messages_checkbox = wx.CheckBox(toolbar,
                                                      ID_SHOW_MESSAGE_LOG,
                                                      " Show message log  ")
        self.show_log_messages_checkbox.SetToolTip(wx.ToolTip("Show or hide "
                                                              "message log"))
        self.show_log_messages_checkbox.SetValue(self.show_message_log)
        toolbar.AddControl(self.show_log_messages_checkbox)
        toolbar.EnableTool(ID_SHOW_LOG, False)
        toolbar.EnableTool(ID_SHOW_REPORT, False)
        toolbar.Realize()
        self._bind_toolbar_events(toolbar)
        return toolbar

    def _bind_toolbar_events(self, toolbar):
        for event, callback, id in ((wx.EVT_TOOL, self.OnShowReport,
                                     ID_SHOW_REPORT), (wx.EVT_TOOL,
                                                       self.OnShowLog,
                                                       ID_SHOW_LOG)):
            toolbar.Bind(event, callback, id=id)
        toolbar.Bind(wx.EVT_CHECKBOX, self.OnAutoSaveCheckbox, self.savecb)
        toolbar.Bind(wx.EVT_CHECKBOX, self.OnShowHideMessageLog,
                     self.show_log_messages_checkbox)
        toolbar.Bind(wx.EVT_CHECKBOX, self.OnPauseOnFailureCheckbox,
                     self.pause_after_failure_cb)
        toolbar.Bind(wx.EVT_CHOICE, self.OnProfileSelection, self.choice)

    def get_current_profile(self):
        return self._test_runner.get_profile(self.choice.GetStringSelection())

    def SetProfile(self, profile):
        """Set the profile to be used to run tests"""
        items = self.choice.GetItems()
        if profile not in items:
            return
        choice_index = items.index(profile)
        self.choice.Select(choice_index)
        p = self._test_runner.get_profile(profile)
        for child in self.config_sizer.GetChildren():
            child.GetWindow().Hide()
            # if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix #TODO fix BoxSizer
            #     self.config_sizer.RemoveChild(child.GetWindow())
            # else:
            #     self.config_sizer.Remove(child.GetWindow())
            self.config_sizer.Detach(child.GetWindow())
        toolbar = p.get_toolbar(self.config_panel)

        if toolbar:
            self.config_sizer.Add(toolbar, 0, wx.EXPAND)
            self.config_sizer.ShowItems(True)
            self.config_sizer.Layout()
            parent = self.config_panel.Parent
            parent_sizer = parent.GetSizer()
            parent_sizer.Layout()

    def _build_notebook_tab(self):
        panel = wx.Panel(self.notebook)
        self.panel = panel
        self.runner_toolbar = self._build_runner_toolbar()
        self.local_toolbar = self._build_local_toolbar()
        self.header_panel = wx.Panel(self.panel)
        self.configPanel = self._build_config_panel(panel)
        self._right_panel = wx.Panel(self.panel)
        self.out = self._create_output_textctrl()
        self.message_log = self._create_output_textctrl() if \
            self.show_message_log else None
        self._clear_output_window()

        self._progress_bar = ProgressBar(self._right_panel)

        right_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        right_panel_sizer.Add(self._progress_bar, 0, wx.EXPAND)
        right_panel_sizer.Add(self.out, 1, wx.EXPAND)
        if self.message_log:
            right_panel_sizer.Add(self.message_log, 1, wx.EXPAND)
        self._right_panel.SetSizer(right_panel_sizer)

        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.header_panel.SetSizer(header_sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.local_toolbar, 0, wx.EXPAND)
        sizer.Add(self.runner_toolbar, 0, wx.EXPAND)
        sizer.Add(self.configPanel, 0, wx.EXPAND | wx.TOP | wx.RIGHT, 4)
        sizer.Add(wx.StaticLine(self.panel), 0, wx.EXPAND | wx.BOTTOM|wx.TOP, 2)
        sizer.Add(self.header_panel, 0, wx.EXPAND | wx.RIGHT, 10)
        sizer.Add(self._right_panel, 1, wx.EXPAND | wx.RIGHT, 8)
        panel.SetSizer(sizer)

        self._process_timer = wx.Timer(self.panel)
        self.panel.Bind(wx.EVT_TIMER, self.OnTimer)

        self.panel.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

        self.add_tab(panel, self.title, allow_closing=False)

    def _create_output_textctrl(self):
        textctrl = OutputStyledTextCtrl(self._right_panel)
        # textctrl.StyleSetFontEncoding(wx.stc.STC_STYLE_DEFAULT, wx.FONTENCODING_CP936)  # DEBUG Chinese wx.) wx.FONTENCODING_SYSTEM
        textctrl.SetScrollWidth(100)
        self._set_margins(textctrl)
        textctrl.SetReadOnly(True)
        return textctrl

    def _set_margins(self, out):
        out.SetMarginLeft(10)
        out.SetMarginWidth(0, 0)
        out.SetMarginWidth(1, 0)
        out.SetMarginWidth(2, 0)
        out.SetMarginWidth(3, 0)

    def _post_result(self, event, *args):
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
        if event == 'end_test':
            self._handle_end_test(args)
        if event == 'report_file':
            self._handle_report_file(args)
        if event == 'log_file':
            self._handle_log_file(args)
        if event == 'start_keyword':
            self._handle_start_keyword(args)
        if event == 'end_keyword':
            self._handle_end_keyword()
        if event == 'log_message':
            self._handle_log_message(args)
        if event == 'paused':
            wx.CallAfter(self._set_paused)
            self._append_to_message_log('<<  PAUSED  >>')
        if event == 'continue':
            wx.CallAfter(self._set_continue)
            self._append_to_message_log('<< CONTINUE >>')

    def _handle_start_test(self, args):
        longname = args[1]['longname']
        self._append_to_message_log('Starting test: %s' % longname)

    def _append_to_message_log(self, text):
        if self.show_message_log:
            self._messages_log_texts.put(text)

    def _handle_end_test(self, args):
        longname = args[1]['longname']
        self._append_to_message_log('Ending test:   %s\n' % longname)
        if args[1]['status'] == 'PASS':
            self._progress_bar.add_pass()
        else:
            self._progress_bar.add_fail()

    def _handle_report_file(self, args):
        self._report_file = args[0]
        wx.CallAfter(self.local_toolbar.EnableTool, ID_SHOW_REPORT, True)

    def _handle_log_file(self, args):
        self._log_file = args[0]
        wx.CallAfter(self.local_toolbar.EnableTool, ID_SHOW_LOG, True)

    def _handle_start_keyword(self, args):
        self._progress_bar.set_current_keyword(args[0])

    def _handle_end_keyword(self):
        self._progress_bar.empty_current_keyword()

    def _handle_log_message(self, args):
        a = args[0]
        if self.show_message_log and LOG_LEVELS[a['level']] >= \
                self._min_log_level_number:
            prefix = '%s : %s : ' % (a['timestamp'], a['level'].rjust(5))
            message = a['message']
            if '\n' in message:
                message = '\n'+message
            self._messages_log_texts.put(prefix+message)

    def _set_running(self):
        self._run_action.disable()
        self._stop_action.enable()
        self._enable_toolbar(False, True)
        self._running = True
        self._test_runner.test_execution_started()

    def _set_paused(self):
        self._run_action.disable()
        self._stop_action.enable()
        self._enable_toolbar(False, False)

    def _set_continue(self):
        self._run_action.disable()
        self._stop_action.enable()
        self._enable_toolbar(False, True)

    def _set_stopped(self):
        self._run_action.enable()
        self._stop_action.disable()
        self._enable_toolbar(True, False)
        self._running = False

    def _enable_toolbar(self, run, paused):
        stop = not run
        debug = stop and not paused
        for id, enabled in ((ID_RUN, run),
                            (ID_RUNDEBUG, run),
                            (ID_STOP, stop),
                            (ID_PAUSE, paused),
                            (ID_CONTINUE, debug),
                            (ID_STEP_NEXT, debug),
                            (ID_STEP_OVER, debug)):
            self.runner_toolbar.EnableTool(id, enabled)


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
        elapsed = time.time()-self._start_time
        message = "elapsed time: %s     pass: %s     fail: %s" % (
            secondsToString(elapsed), self._pass, self._fail)
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

    def _fix_size(self, text, max_length):
        if len(text) <= max_length:
            return text
        return '...'+text[3-max_length:]


class OutputStyledTextCtrl(wx.stc.StyledTextCtrl):

    def __init__(self, parent):
        wx.stc.StyledTextCtrl.__init__(self, parent, wx.ID_ANY,
                                       style=wx.SUNKEN_BORDER)
        self.stylizer = OutputStylizer(self, parent.GetParent().GetParent()._app.settings)
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
            # print("DEBUG: UnicodeDecodeError at update scroll,
            # testrunnerplugin, string is %s\n" % string)
            pass


class OutputStylizer(object):
    def __init__(self, editor, settings):
        self.editor = editor
        self.settings = settings._config_obj['Plugins']['Test Runner']
        self._ensure_default_font_is_valid()
        self._set_styles()
        PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)

    def OnSettingsChanged(self, data):
        '''Redraw colors and font if settings are modified'''
        section, setting = data.keys
        if section == 'Test Runner':
            self._set_styles()

    def _set_styles(self):
        '''Sets plugin styles'''
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

    def _get_style_string(self, back, fore, size, face):
        return ','.join('%s:%s' % (name, value)
                        for name, value in locals().items() if value)

    def _ensure_default_font_is_valid(self):
        '''Checks if default font is installed'''
        default_font = self.settings.get('font face')
        if default_font not in ReadFonts():
            sys_font = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT)
            self.settings['font face'] = sys_font.GetFaceName()


# stole this off the internet. Nifty.
def secondsToString(t):
    """Convert a number of seconds to a string of the form HH:MM:SS"""
    return "%d:%02d:%02d" % \
        reduce(lambda ll, b: divmod(ll[0], b) + ll[1:], [(t,), 60, 60])


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
