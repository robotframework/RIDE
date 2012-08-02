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


'''A plugin for running tests from within RIDE

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
'''
import subprocess
from Queue import Queue, Empty
import tempfile
import datetime
import time
import SocketServer
import os
import sys
import threading
import atexit
import shutil
import signal
import posixpath
import re
import codecs
from posixpath import curdir, sep, pardir, join
from robot.utils.encoding import SYSTEM_ENCODING
from robot.utils.encodingsniffer import DEFAULT_OUTPUT_ENCODING
from robotide.contrib.testrunner.runprofiles import CustomScriptProfile
from robotide.controller.testexecutionresults import TestExecutionResults
from robotide.publish.messages import (RideDataFileSet, RideDataFileRemoved, RideFileNameChanged,
                                       RideTestSelectedForRunningChanged, RideTestRunning, RideTestPassed,
                                       RideTestFailed, RideTestExecutionStarted)

ON_POSIX = 'posix' in sys.builtin_module_names

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

import wx
import wx.stc
from wx.lib.embeddedimage import PyEmbeddedImage

from robotide.pluginapi import Plugin, ActionInfo
from robotide.publish import RideTestCaseAdded, RideOpenSuite, RideSuiteAdded, \
                              RideItemNameChanged, RideTestCaseRemoved
from robotide.contrib.testrunner import runprofiles
from robotide.widgets import Label


ID_RUN = wx.NewId()
ID_STOP = wx.NewId()
ID_SHOW_REPORT = wx.NewId()
ID_SHOW_LOG = wx.NewId()
ID_AUTOSAVE = wx.NewId()
STYLE_STDERR = 2


try:
    from os.path import relpath
except ImportError:
    # the python 2.6 os.path package provides a relpath() function,
    # but we're running 2.5 so we have to roll our own
    def relpath(path, start=curdir):
        """Return a relative version of a path"""
        if not path:
            raise ValueError("no path specified")
        start_list = posixpath.abspath(start).split(sep)
        path_list = posixpath.abspath(path).split(sep)
        # Work out how much of the filepath is shared by start and path.
        i = len(posixpath.commonprefix([start_list, path_list]))
        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return curdir
        return join(*rel_list)

def _RunProfile(name, run_prefix):
    return type('Profile', (runprofiles.PybotProfile,),
                {'name': name, 'get_command': lambda self: run_prefix})


class TestRunnerPlugin(Plugin):
    """A plugin for running tests from within RIDE"""
    defaults = {"auto_save": False,
                "profile": "pybot",
                "sash_position": 200,
                "runprofiles": [('jybot', 'jybot' + ('.bat' if os.name == 'nt' else ''))]}
    report_regex = re.compile("^Report: {2}(.*\.html)$", re.MULTILINE)
    log_regex = re.compile("^Log: {5}(.*\.html)$", re.MULTILINE)
    title = "Run"

    def __init__(self, application=None):
        Plugin.__init__(self, application, initially_enabled=True,
                        default_settings=self.defaults)
        self.version = "3.01"
        self.metadata = {"url": "http://code.google.com/p/robotframework-ride/wiki/TestRunnerPlugin"}
        self._reload_timer = None
        self._application = application
        self._frame = application.frame
        self._process = None
        self._pid_to_kill = None
        self._tmpdir = None
        self._report_file = None
        self._log_file = None
        self.profiles = {}
        self._controls = {}
        self._server = None
        self._server_thread = None
        self._port = None
        self._running = False
        self.register_shortcut('Ctrl-C', self._copy_from_out)
        self._currently_executing_keyword = None
        self._tests_to_run = set()
        self._running_results = TestExecutionResults()

    def _copy_from_out(self, event):
        if self.notebook.current_page_title != self.title:
            return
        if not self.out.GetSTCFocus():
            return
        self.out.Copy()

    def enable(self):
        self.tree.set_checkboxes_for_tests()
        self._read_run_profiles()
        self._register_actions()
        self._build_ui()
        self.SetProfile(self.profile)
        self._subscribe_to_events()
        self._start_listener_server()
        self._create_temporary_directory()
        self._set_stopped()

    def _register_actions(self):
        run_action_info = ActionInfo("Tools", "Run Test Suite", self.OnRun, None,
                                     "F8", getRobotBitmap(), "Run the selected tests")
        self._run_action = self.register_action(run_action_info)
        stop_action_info = ActionInfo("Tools", "Stop Running", self.OnStop, None,
                                      "Ctrl-F8", getProcessStopBitmap(), "Stop a running test")
        self._stop_action = self.register_action(stop_action_info)

    def _read_run_profiles(self):
        self._read_run_profiles_from_config()
        self._read_run_profiles_from_classes()

    def _read_run_profiles_from_config(self):
        #Have to keep reference so that these classes are not garbage collected
        self._profile_classes_from_config = [_RunProfile(name, run_prefix)
                                             for name, run_prefix in self.runprofiles]

    def _read_run_profiles_from_classes(self):
        for profile in self._get_all_subclasses(runprofiles.BaseProfile):
            self.profiles[profile.name] = profile(plugin=self)

    def _get_all_subclasses(self, class_):
        classes = []
        for sub_class in class_.__subclasses__():
            classes += [sub_class] + self._get_all_subclasses(sub_class)
        return classes

    def _subscribe_to_events(self):
        self.subscribe(self.OnTestSelectedForRunningChanged, RideTestSelectedForRunningChanged)
        self.subscribe(self.OnOpenSuite, RideOpenSuite)

    def OnTestSelectedForRunningChanged(self, message):
        if message.running:
            self._test_names_to_run.add(message.item.longname)
        else:
            self._test_names_to_run.discard(message.item.longname)

    def OnOpenSuite(self, message):
        self._test_names_to_run = set()

    def _start_listener_server(self):
        self._server = RideListenerServer(RideListenerHandler,
                                          self._post_result)
        self._server_thread = threading.Thread(target=self._server.serve_forever)
        self._server_thread.setDaemon(True)
        self._server_thread.start()
        self._port = self._server.server_address[1]

    def _create_temporary_directory(self):
        self._tmpdir = tempfile.mkdtemp(".d", "RIDE")
        atexit.register(self._remove_temporary_directory)
        # this plugin creates a temporary directory which _should_
        # get reaped at exit. Sometimes things happen which might
        # cause it to not get deleted. Maybe this would be a good
        # place to check for temporary directories that match the
        # signature and delete them if they are more than a few
        # days old...

    def _remove_temporary_directory(self):
        if os.path.exists(self._tmpdir):
            shutil.rmtree(self._tmpdir)

    def disable(self):
        self._remove_from_notebook()
        self._server = None
        self.unsubscribe_all()
        self.unregister_actions()

    def OnClose(self, evt):
        '''Shut down the running services and processes'''
        if self._process:
            self._process.kill(force=True)
        if self._process_timer:
            self._process_timer.Stop()
        if self._server:
            self._server.shutdown()

    def OnAutoSaveCheckbox(self, evt):
        '''Called when the user clicks on the "Auto Save" checkbox'''
        self.save_setting("auto_save", evt.IsChecked())

    def OnStop(self, event):
        '''Called when the user clicks the "Stop" button

        This sends a SIGINT to the running process, with the
        same effect as typing control-c when running from the
        command line.
        '''
        if self._process:
            self._output("process %s killed\n" % self._process.kill())
            self._set_stopped()
            self._progress_bar.Stop()
            self._process_timer.Stop()
            self._process = None

    def OnRun(self, event):
        '''Called when the user clicks the "Run" button'''
        if not self._can_start_running_tests():
            return
        self._initialize_ui_for_running()
        command = self._format_command(self._get_command())
        self._output("command: %s\n" % command)
        try:
            self._process = Process(self._get_current_working_dir())
            self._process.run_command(command)
            self._process_timer.Start(41) # roughly 24fps
            self._set_running()
            self._progress_bar.Start()
        except Exception, e:
            #FIXME: Dead code?
            self._set_stopped()
            self._output(str(e))
            wx.MessageBox("Could not start running tests.", "Error", wx.ICON_ERROR)

    def _get_current_working_dir(self):
        profile = self.get_current_profile()
        if profile.name == CustomScriptProfile.name:
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
        ret = wx.MessageBox('There are unsaved modifications.\n'
                            'Do you want to save all changes and run the tests?',
                            'Unsaved Modifications',
                            wx.ICON_QUESTION|wx.YES_NO)
        return ret == wx.YES

    def _initialize_ui_for_running(self):
        self._show_notebook_tab()
        self._clear_output_window()
        self.local_toolbar.EnableTool(ID_SHOW_REPORT, False)
        self.local_toolbar.EnableTool(ID_SHOW_LOG, False)
        self._report_file = self._log_file = None

    def _clear_output_window(self):
        self.out.SetReadOnly(False)
        self.out.ClearAll()
        self.out.SetReadOnly(True)

    def OnShowReport(self, evt):
        '''Called when the user clicks on the "Report" button'''
        if self._report_file:
            wx.LaunchDefaultBrowser("file:%s" % os.path.abspath(self._report_file))

    def OnShowLog(self, evt):
        '''Called when the user clicks on the "Log" button'''
        if self._log_file:
            wx.LaunchDefaultBrowser("file:%s" % os.path.abspath(self._log_file))

    def OnProfileSelection(self, event):
        self.save_setting("profile", event.GetString())
        self.SetProfile(self.profile)

    def OnProcessEnded(self, evt):
        output, errors = self._process.get_output(), self._process.get_errors()
        self._output(output)
        self._read_report_and_log_from_stdout_if_needed()
        if len(errors) > 0:
            self._output("unexpected error: " + errors)
        self._progress_bar.Stop()
        if self._process_timer:
            self._process_timer.Stop()

        now = datetime.datetime.now()
        self._output("\ntest finished %s" % now.strftime("%c"))
        self._set_stopped()
        self._process = None

    def _read_report_and_log_from_stdout_if_needed(self):
        output = self.out.GetText()
        if not self._report_file:
            self._report_file = self._get_report_or_log(output, self.report_regex)
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
        if not self._process.is_alive():
            self.OnProcessEnded(None)
            return
        out_buffer, err_buffer = self._process.get_output(), self._process.get_errors()
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

    def GetLastOutputChar(self):
        '''Return the last character in the output window'''
        pos = self.out.PositionBefore(self.out.GetLength())
        char = self.out.GetCharAt(pos)
        return chr(char)

    def _format_command(self, argv):
        '''Quote a list as if it were a command line command

        This isn't perfect but seems to work for the normal use
        cases. I'm not entirely sure what the perfect algorithm
        is since *nix and windows have different quoting
        behaviors.
        '''
        result = []
        for arg in argv:
            if "'" in arg or " " in arg:
                # for windows, if there are spaces we need to use
                # double quotes. Single quotes cause problems
                result.append('"%s"' % arg)
            elif '"' in arg:
                result.append("'%s'" % arg)
            else:
                result.append(arg)
        return " ".join(result)

    def _show_notebook_tab(self):
        '''Show the Run notebook tab'''
        if not self.panel:
            self._build_notebook_tab()
            self._reload_model()
        self.show_tab(self.panel)

    def _AppendText(self, string, source="stdout"):
        if not self.panel:
            return
        try:
            width, _ = self.out.GetTextExtent(string)
            if self.out.GetScrollWidth() < width+50:
                self.out.SetScrollWidth(width+50)
        except UnicodeDecodeError:
            # I don't know what unicode data it is complaining about,
            # but I think the best thing is just to ignore it
            pass

        # we need this information to decide whether to autoscroll or not
        new_text_start = self.out.GetLength()
        linecount = self.out.GetLineCount()
        lastVisibleLine = self.out.GetFirstVisibleLine() + self.out.LinesOnScreen() - 1

        self.out.SetReadOnly(False)
        try:
            self.out.AppendText(string)
        except UnicodeDecodeError,e:
            # I'm not sure why I sometimes get this, and I don't know what I can
            # do other than to ignore it.
            pass

        new_text_end = self.out.GetLength()

        self.out.StartStyling(new_text_start, 0x1f)
        if source == "stderr":
            self.out.SetStyling(new_text_end-new_text_start, STYLE_STDERR)

        self.out.SetReadOnly(True)
        if lastVisibleLine >= linecount-4:
            linecount = self.out.GetLineCount()
            self.out.ScrollToLine(linecount)

    def _add_tmp_outputdir_if_not_given_by_user(self, command, standard_args):
        if "--outputdir" not in command and "-d" not in command:
            standard_args.extend(["--outputdir", self._tmpdir])

    def _create_standard_args(self, command, profile):
        standard_args = []
        standard_args.extend(profile.get_custom_args())
        self._add_tmp_outputdir_if_not_given_by_user(command, standard_args)
        self._add_pythonpath_if_in_settings_and_not_given_by_user(command,
                                                                  standard_args)
        standard_args.extend(["--monitorcolors", "off"])
        standard_args.extend(["--monitorwidth", self._get_monitor_width()])
        for tc in self._test_names_to_run:
            standard_args += ['--test', tc]
        return standard_args

    def _get_command(self):
        '''Return the command (as a list) used to run the test'''
        profile = self.get_current_profile()
        command = profile.get_command_prefix()[:]
        argfile = os.path.join(self._tmpdir, "argfile.txt")
        command.extend(["--argumentfile", argfile])
        command.extend(["--listener", self._get_listener_to_cmd()])
        command.append(self._get_suite_source_for_command())
        self._write_argfile(argfile, self._create_standard_args(command, profile))
        return command

    def _get_suite_source_for_command(self):
        cur = os.path.abspath(os.path.curdir)
        source = os.path.abspath(self.model.suite.source)
        if not self._is_same_drive(cur, source):
            return source
        return os.path.abspath(self.model.suite.source)

    def _is_same_drive(self, source1, source2):
        return os.path.splitdrive(source1)[0] == os.path.splitdrive(source2)[0]

    def _write_argfile(self, argfile, args):
        f = codecs.open(argfile, "w", "utf-8")
        f.write("\n".join(args))
        f.close()

    def _add_pythonpath_if_in_settings_and_not_given_by_user(self, command, standard_args):
        if '--pythonpath' in command:
            return
        if '-P' in command:
            return
        pythonpath = self.global_settings.get('pythonpath', None)
        if not pythonpath:
            return
        standard_args.extend(['--pythonpath', ':'.join(pythonpath)])

    def _get_listener_to_cmd(self):
        return os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "SocketListener.py") + ":%s" % self._port

    def _get_monitor_width(self):
        # robot wants to know a fixed size for output, so calculate the
        # width of the window based on average width of a character. A
        # little is subtracted just to make sure there's a little margin
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
        panel = wx.Panel(parent, wx.ID_ANY, style=wx.BORDER_NONE|wx.TAB_TRAVERSAL)
        self.config_sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(self.config_sizer)
        self.config_panel = panel
        return panel

    def _output(self, string, source="stdout"):
        '''Put output to the text control'''
        self._AppendText(string, source)

    def _build_local_toolbar(self):
        toolbar = wx.ToolBar(self.panel, wx.ID_ANY, style=wx.TB_HORIZONTAL|wx.TB_HORZ_TEXT)
        profileLabel = Label(toolbar, label="Execution Profile:  ")
        choices = sorted(self.profiles.keys())
        self.choice = wx.Choice(toolbar, wx.ID_ANY, choices=choices)
        self.choice.SetToolTip(wx.ToolTip("Choose which method to use for running the tests"))
        toolbar.AddControl(profileLabel)
        toolbar.AddControl(self.choice)
        toolbar.AddSeparator()
        reportImage = getReportIconBitmap()
        logImage = getLogIconBitmap()
        toolbar.AddLabelTool(ID_RUN,"Start", getRobotBitmap(), shortHelp="Start robot",
                             longHelp="Start running the robot test suite")
        toolbar.AddLabelTool(ID_STOP,"Stop", getProcessStopBitmap(),
                             shortHelp="Stop a running test",
                             longHelp="Stop a running test")
        toolbar.AddSeparator()
        toolbar.AddLabelTool(ID_SHOW_REPORT, " Report", reportImage,
                             shortHelp = "View Robot Report in Browser")
        toolbar.AddLabelTool(ID_SHOW_LOG, " Log", logImage,
                             shortHelp = "View Robot Log in Browser")
        toolbar.AddSeparator()
        # the toolbar API doesn't give us a way to specify padding which
        # is why the label has a couple spaces after the colon. gross,
        # but effective.
        self.savecb = wx.CheckBox(toolbar, ID_AUTOSAVE, "Autosave")
        self.savecb.SetToolTip(wx.ToolTip("Automatically save all changes before running"))
        self.savecb.SetValue(self.auto_save)
        toolbar.AddControl(self.savecb)

        toolbar.EnableTool(ID_SHOW_LOG, False)
        toolbar.EnableTool(ID_SHOW_REPORT, False)

        toolbar.Realize()
        toolbar.Bind(wx.EVT_TOOL, self.OnRun, id=ID_RUN)
        toolbar.Bind(wx.EVT_TOOL, self.OnStop, id=ID_STOP)
        toolbar.Bind(wx.EVT_TOOL, self.OnShowReport, id=ID_SHOW_REPORT)
        toolbar.Bind(wx.EVT_TOOL, self.OnShowLog, id=ID_SHOW_LOG)
        toolbar.Bind(wx.EVT_CHECKBOX, self.OnAutoSaveCheckbox, self.savecb)
        toolbar.Bind(wx.EVT_CHOICE, self.OnProfileSelection, self.choice)

        return toolbar

    def get_current_profile(self):
        profile = self.choice.GetStringSelection()
        p = self.profiles[profile]
        return p

    def SetProfile(self, profile):
        '''Set the profile to be used to run tests'''
        items = self.choice.GetItems()
        if profile not in items:
            return
        choice_index = items.index(profile)
        self.choice.Select(choice_index)
        p = self.profiles[profile]
        for child in self.config_sizer.GetChildren():
            child.GetWindow().Hide()
            self.config_sizer.Remove(child.GetWindow())
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
        self.local_toolbar = self._build_local_toolbar()
        self.header_panel = wx.Panel(self.panel)
        self.configPanel = self._build_config_panel(panel)
        self._right_panel = wx.Panel(self.panel)
        self.out = wx.stc.StyledTextCtrl(self._right_panel, wx.ID_ANY, style=wx.SUNKEN_BORDER)
        font=wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FIXED_FONT)
        if not font.IsFixedWidth():
            # fixed width fonts are typically a little bigger than their variable width
            # peers so subtract one from the point size.
            font = wx.Font(font.GetPointSize()-1, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        face = font.GetFaceName()
        size = font.GetPointSize()
        self.out.SetFont(font)
        self.out.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,"face:%s,size:%d" % (face, size))
        self.out.StyleSetSpec(STYLE_STDERR, "fore:#b22222") # firebrick
        self.out.SetScrollWidth(100)

        self.out.SetMarginLeft(10)
        self.out.SetMarginWidth(0,0)
        self.out.SetMarginWidth(1,0)
        self.out.SetMarginWidth(2,0)
        self.out.SetMarginWidth(3,0)
        self.out.SetReadOnly(True)
        self._clear_output_window()

        self._progress_bar = ProgressBar(self._right_panel)

        right_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        right_panel_sizer.Add(self._progress_bar, 0, wx.EXPAND)
        right_panel_sizer.Add(self.out, 1, wx.EXPAND)
        self._right_panel.SetSizer(right_panel_sizer)

        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.header_panel.SetSizer(header_sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.local_toolbar, 0, wx.EXPAND)
        sizer.Add(self.configPanel, 0, wx.EXPAND|wx.TOP|wx.RIGHT, 4)
        sizer.Add(wx.StaticLine(self.panel), 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 2)
        sizer.Add(self.header_panel, 0, wx.EXPAND|wx.RIGHT, 10)
        sizer.Add(self._right_panel, 1, wx.EXPAND|wx.RIGHT, 8)
        panel.SetSizer(sizer)

        self._process_timer = wx.Timer(self.panel)
        self.panel.Bind(wx.EVT_TIMER, self.OnTimer)
        self.panel.Bind(wx.EVT_END_PROCESS, self.OnProcessEnded)

        self.panel.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

        self.add_tab(panel, self.title, allow_closing=False)

    def _post_result(self, event, *args):
        '''Endpoint of the listener interface

        This is called via the listener interface. It has an event such as "start_suite",
        "start_test", etc, along with metadata about the event. We use this data to update
        the tree and statusbar.'''
        if not self.panel:
            # this should only happen if the notebook tab got deleted
            # out from under us. In the immortal words of Jar Jar
            # Binks, "How rude!"
            return

        if event == 'pid':
            self._pid_to_kill = int(args[0])
        if event == 'start_test':
            _, attrs = args
            longname = attrs['longname']
            self._running_results.set_running(self._get_test_controller(longname))
        if event == 'start_suite':
            _, attrs = args
            longname = attrs['longname']
        if event == 'end_test':
            _, attrs = args
            longname = attrs['longname']
            if attrs['status'] == 'PASS':
                self._progress_bar.Pass()
                self._running_results.set_passed(self._get_test_controller(longname))
            else:
                self._progress_bar.Fail()
                self._running_results.set_failed(self._get_test_controller(longname))
        if event == 'end_suite':
            pass
        if event == 'report_file':
            self._report_file = args[0]
            self.local_toolbar.EnableTool(ID_SHOW_REPORT, True)

        if event == 'log_file':
            self._log_file = args[0]
            self.local_toolbar.EnableTool(ID_SHOW_LOG, True)

        if event == 'start_keyword':
            self._progress_bar.set_current_keyword(args[0])
        if event == 'end_keyword':
            self._progress_bar.empty_current_keyword()

    def _get_test_controller(self, longname):
        return self._application.model.find_controller_by_longname(longname)

    def _set_state(self, state):
        if state == "running":
            self._set_running()
        else:
            self._set_stopped()

    def _set_running(self):
        self._run_action.disable()
        self._stop_action.enable()
        self.local_toolbar.EnableTool(ID_RUN, False)
        self.local_toolbar.EnableTool(ID_STOP, True)
        self._running = True
        self._running_results.test_execution_started()


    def _set_stopped(self):
        self._run_action.enable()
        self._stop_action.disable()
        self.local_toolbar.EnableTool(ID_RUN, True)
        self.local_toolbar.EnableTool(ID_STOP, False)
        self._running = False


class ProgressBar(wx.Panel):
    '''A progress bar for the test runner plugin'''
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._gauge = wx.Gauge(self, size=(100, 10))
        self._label = Label(self)
        self._sizer.Add(self._label, 1, wx.EXPAND|wx.LEFT, 10)
        self._sizer.Add(self._gauge, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
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
        self._current_keywords.pop()

    def OnTimer(self, event):
        '''A handler for timer events; it updates the statusbar'''
        self._gauge.Show()
        self._gauge.Pulse()
        self._update_message()

    def Start(self):
        '''Signals the start of a test run; initialize progressbar.'''
        self._initialize_state()
        self._start_time = time.time()
        self._gauge.Show()
        self._sizer.Layout()
        self.SetBackgroundColour(self._default_colour)
        self._timer.Start(50)

    def Stop(self):
        '''Signals the end of a test run'''
        self._gauge.Hide()
        self._timer.Stop()

    def Pass(self):
        '''Add one to the passed count'''
        self._pass += 1

    def Fail(self):
        '''Add one to the failed count'''
        self._fail += 1

    def _update_message(self):
        '''Update the displayed elapsed time, passed and failed counts'''
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
        return '     current keyword: '+self._fix_size(' -> '.join(self._current_keywords), 50)

    def _fix_size(self, text, max_length):
        if len(text) <= max_length:
            return text
        return '...'+text[3-max_length:]


# The following two classes implement a small line-buffered socket
# server. It is designed to run in a separate thread, read data
# from the given port and update the UI -- hopefully all in a
# thread-safe manner.
class RideListenerServer(SocketServer.TCPServer):
    """Implements a simple line-buffered socket server"""
    allow_reuse_address = True
    def __init__(self, RequestHandlerClass, callback):
        SocketServer.TCPServer.__init__(self, ("",0), RequestHandlerClass)
        self.callback = callback

class RideListenerHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        unpickler = pickle.Unpickler(self.request.makefile('r'))
        while True:
            try:
                (name, args) = unpickler.load()
                wx.CallAfter(self.server.callback, name, *args)
            except (EOFError, IOError):
                # I should log this...
                break


class Process(object):

    def __init__(self, cwd):
        self._process = None
        self._error_stream = None
        self._output_stream = None
        self._cwd = cwd

    def run_command(self, command):
        # We need to supply an stdin for subprocess, because otherways in pythonw
        # subprocess will try using sys.stdin which will cause an error in windows
        self._process = subprocess.Popen(
            command.encode(SYSTEM_ENCODING),
            bufsize=0,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            shell=True,
            cwd=self._cwd.encode(SYSTEM_ENCODING))
        self._process.stdin.close()
        self._output_stream = StreamReaderThread(self._process.stdout)
        self._error_stream = StreamReaderThread(self._process.stderr)
        self._output_stream.run()
        self._error_stream.run()

    def get_output(self):
        return self._output_stream.pop()

    def get_errors(self):
        return self._error_stream.pop()

    def is_alive(self):
        return self._process.poll() is None

    def kill(self, force=False):
        if not self._process:
            return
        if force:
            self._process.kill()
        pid = self._process.pid
        if pid:
            try:
                if os.name == 'nt' and sys.version_info < (2,7):
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    handle = kernel32.OpenProcess(1, 0, pid)
                    kernel32.TerminateProcess(handle, 0)
                else:
                    os.kill(pid, signal.SIGINT)
            except OSError:
                pass
        return pid

class StreamReaderThread(object):

    def __init__(self, stream):
        self._queue = Queue()
        self._thread = None
        self._stream = stream

    def run(self):
        self._thread = threading.Thread(target=self._enqueue_output, args=(self._stream,))
        self._thread.daemon = True
        self._thread.start()

    def _enqueue_output(self, out):
        for line in iter(out.readline, b''):
            self._queue.put(line)

    def pop(self):
        result = ""
        for _ in xrange(self._queue.qsize()):
            try:
                result += self._queue.get_nowait()
            except Empty:
                pass
        return result.decode(DEFAULT_OUTPUT_ENCODING)


# stole this off the internet. Nifty.
def secondsToString(t):
    '''Convert a number of seconds to a string of the form HH:MM:SS'''
    return "%d:%02d:%02d" % \
        reduce(lambda ll,b : divmod(ll[0],b) + ll[1:],
            [(t,),60, 60])



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

