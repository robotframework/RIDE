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
from robotide.publish.messages import RideSuiteAdded


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

import tempfile
import datetime, time
import SocketServer
import socket
import os
import sys
import threading
import atexit
import shutil
import signal
from robot.parsing.model import TestCase
from robotide.pluginapi import Plugin, ActionInfo
from robotide.publish import (RideUserKeywordAdded, RideTestCaseAdded,
                              RideOpenSuite, RideOpenResource,
                              RideItemNameChanged, RideTestCaseRemoved)
import wx
import wx.stc
from wx.lib.embeddedimage import PyEmbeddedImage

try:
    import cPickle as pickle
except ImportError, e:
    import pickle as pickle


ID_RUN = wx.NewId()
ID_STOP = wx.NewId()
ID_SHOW_REPORT = wx.NewId()
ID_SHOW_LOG = wx.NewId()
ID_AUTOSAVE = wx.NewId()

STYLE_STDERR=2

sys.path.insert(0, os.path.dirname(__file__))
from TestSuiteTreeCtrl import TestSuiteTreeCtrl
import runprofiles
import asyncproc
sys.path.pop(0)


def _RunProfile(name, run_prefix):
    return type('Profile', (runprofiles.BaseProfile,),
                {'name': name, 'get_command_prefix': lambda self: [run_prefix]})


class TestRunnerPlugin(Plugin):
    """A plugin for running tests from within RIDE"""
    defaults = { "auto_save": False,
                "profile": "pybot",
                "custom_script": "",
                "include_tags": "",
                "exclude_tags": "",
                "apply_include_tags": False,
                "apply_exclude_tags": False,
                "port": 5010,
                "sash_position": 200,
                "runprofiles": [('jybot', 'jybot' + ('.bat' if os.name == 'nt' else ''))]}

    def __init__(self, application=None):
        Plugin.__init__(self, application, initially_enabled=True,
                        default_settings=self.defaults)
        self.version = "3.0"
        self.metadata = {"url": "http://code.google.com/p/robotframework-ride/wiki/TestRunnerPlugin"}

        self._application = application
        self._frame = application.frame
        self._process = None
        self._tmpdir = None
        self._report_file = None
        self._log_file = None
        self.profiles = {}
        self._controls = {}
        self._server = None
        self._server_thread = None
        self._port = None
        self._running = False

    def enable(self):
        self._read_run_profiles()
        self._register_actions()
        self._build_ui()
        self.SetProfile(self.profile)
        self._subscribe_to_events()
        self._start_listener_server()
        self._load_tree_if_data_is_open()
        self._create_temporary_directory()
        self._set_state("stopped")

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
        for profile in runprofiles.BaseProfile.__subclasses__():
            self.profiles[profile.name] = profile(plugin=self)

    def _subscribe_to_events(self):
        self.subscribe(self.OnModelChanged, *[RideUserKeywordAdded,
                                              RideTestCaseAdded,
                                              RideOpenSuite,
                                              RideOpenResource,
                                              RideItemNameChanged,
                                              RideTestCaseRemoved,
                                              RideSuiteAdded])

    def _start_listener_server(self):
        port = self.port
        while not self._server and port <= port+10:
            try:
                self._server = RideListenerServer(("",port), RideListenerHandler,
                                                  self._post_result)
            except socket.error:
                port += 1
                continue
            self._server_thread = threading.Thread(target=self._server.serve_forever)
            self._server_thread.setDaemon(True)
            self._server_thread.start()
            self._port = port
        if not self._server:
            raise RuntimeError("Cannot start the RideListenerServer.")

    def _load_tree_if_data_is_open(self):
        if self.model is not None and self.model.suite is not None:
            self.OnModelChanged()

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

    def OnModelChanged(self, *args):
        '''Update the display to reflect a changed model'''
        if not self._running:
            # This is an awful hack. RIDE seems to have a timing issue
            # -- sometimes this gets called before the model has
            # actually changed. So, we'll wait before doing any real
            # work.
            wx.CallLater(750, self._reload_model)

    def OnClose(self, evt):
        '''Shut down the running services and processes'''
        if self._process:
            self._kill_process()
        if self._process_timer:
            self._process_timer.Stop()

    def _kill_process(self):
        if self._pid_to_kill:
            os.kill(self._pid_to_kill, signal.SIGINT)
            self._output("process %s killed\n" % self._pid_to_kill)
        self._pid_to_kill = None

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
            self._kill_process()

    def OnRun(self, event):
        '''Called when the user clicks the "Run" button'''
        if not self._can_start_running_tests():
            return
        self._initialize_ui_for_running()
        command = self._get_command()
        self._output("working directory: %s\n" % os.getcwd())
        self._output("command: %s\n" % self._format_command(command))
        try:
            self._process = asyncproc.Process(command)
            self._set_state("running")
            self._progress_bar.Start()
            wx.CallAfter(self._poll_process_output)
        except Exception, e:
            self._set_state("stopped")
            self._output(str(e))
            wx.MessageBox("Could not start running tests.", "Error", wx.ICON_ERROR)

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
        self._tree.Reset()
        self._clear_output_window()

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

    def OnSplitterSashChanged(self, evt):
        sash_position = self.splitter.GetSashPosition()
        # this is a gross hack. For some reason yet to be determined, sometimes
        # a value of 7 is getting saved. Weird.
        if sash_position > 10:
            self.save_setting("sash_position", sash_position)

    def OnProfileSelection(self, event):
        self.save_setting("profile", event.GetString())
        self.SetProfile(self.profile)

    def OnDoubleClick(self, event):
        '''Handle double-click events on the tree

        Ideally this would always open the object in the editor
        but it uses a method that doesn't quite work. It works
        on test cases by accident, and test suites that are two
        levels deep, but it won't work on suites one level deep.
        *sigh*

        '''
        item = self._tree.GetSelection()
        tcuk = self._tree.GetItemPyData(item).tcuk
        # the select_user_keyword_node works for keywords and
        # test cases, but it doesn't always work for test suites
        if isinstance(tcuk, TestCase):
            try:
                self._frame.tree.select_user_keyword_node(tcuk)
                tab = self._application._find_edit_tab_for_tcuk(tcuk)
                if tab is not None:
                    self._frame.notebook.show_tab(tab)
            except Exception, e:
                # <shrug> oh well.
                pass
        event.Skip()

    def OnTreePaint(self, event):
        '''Reposition the little menubutton when the tree is repainted'''
        self._reposition_menubutton()
        event.Skip()

    def OnTreeResize(self, event):
        '''Reposition the little menubutton with the tree is resized'''
        event.Skip()
        self._reposition_menubutton()

    def OnMenuButton(self, event):
        '''Show the menu associated with the menu button'''
        (x,y) = self._menubutton.GetPosition()
        (_,h) = self._menubutton.GetSize()
        self._tree.PopupMenu(self._tree_menu, (x,y+h))

    def GetLastOutputChar(self):
        '''Return the last character in the output window'''
        pos = self.out.PositionBefore(self.out.GetLength())
        char = self.out.GetCharAt(pos)
        return chr(char)

    def _reload_model(self):
        '''Redraw the tree when the model changes'''
        self._tree.SetDataModel(self.model)
        if not self._running:
            wx.CallAfter(self._tree.Redraw)

    def _format_command(self, argv):
        '''Quote a list as if it were a command line command

        This is purely for aesthetics -- it takes a list of arguments
        and quotes them as you probably would have to do if you ran this        toolbar.AddControl(self.choice)
        from a command line
        '''
        result = []
        for arg in argv:
            if "'" in arg:
                result.append('"%s"' % arg)
            elif '"' in arg or " " in arg:
                result.append("'%s'" % arg)
            else:
                result.append(arg)
        return " ".join(result)

    def _poll_process_output(self):
        '''Periodically display output from the process'''
        stdout = self._consume_stdout()
        if stdout:
            self._output(stdout, source="stdout")
        stderr = self._consume_stderr()
        if stderr:
            self._output_with_ensured_newline(stderr, source="stderr")
        if self._is_process_alive():
            wx.CallLater(500, self._poll_process_output)
        else:
            self._finish_process_output()

    def _finish_process_output(self):
        self._progress_bar.Stop()
        now = datetime.datetime.now()
        self._output("\ntest finished %s" % now.strftime("%c"))
        self._set_state("stopped")
        self._process = None

    def _consume_stdout(self):
        return self._process.read()

    def _consume_stderr(self):
        return self._process.readerr()

    @property
    def _output_with_ensured_newline(self):
        self._ensure_newline_in_output()
        return self._output

    def _ensure_newline_in_output(self):
        if self.GetLastOutputChar() != "\n":
            # Robot prints partial lines to stdout to make the
            # interactive experience better. It all goes to
            # heck in a handbasket if something shows up on
            # stderr. So, to fix that we'll add a newline if
            # the previous character isn't a newline.
            self._output("\n", source="stdout")

    def _is_process_alive(self):
        return self._process.poll() is None

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

    def _get_command(self):
        '''Return the command (as a list) used to run the test'''
        listener = os.path.join(os.path.dirname(__file__), 
                                "SocketListener.py")+ ":%s" % self._port

        profile = self.get_current_profile()
        command = profile.get_command_prefix()
        custom_args = profile.get_custom_args()

        argfile = os.path.join(self._tmpdir, "argfile.txt")
        self._relpath(self.model.suite.source)
        command.extend(["--argumentfile", argfile])
        command.extend(["--listener", listener])
        command.append(self._relpath(self.model.suite.source))

        # robot wants to know a fixed size for output, so calculate the
        # width of the window based on average width of a character. A
        # little is subtracted just to make sure there's a little margin
        out_width, _ = self.out.GetSizeTuple()
        char_width = self.out.GetCharWidth()
        monitorwidth = int(out_width/char_width)-10

        standard_args = []
        standard_args.extend(["--outputdir",self._tmpdir])
        standard_args.extend(["--monitorcolors","off"])
        standard_args.extend(["--monitorwidth",str(monitorwidth)])

        for (suite, test) in self._tree.GetCheckedTestsByName():
            standard_args.extend(["--suite", suite, "--test", test])

        f = open(argfile, "w")
        f.write("\n".join(custom_args) + "\n")
        f.write("\n".join(standard_args))
        f.close()

        return command

    # the python 2.6 os.path package provides a relpath() function,
    # but we're running 2.5 so we have to roll our own
    def _relpath(self, path):
        """Generate a relative path"""
        path = path.rstrip("/")
        start = os.getcwd()
        if path == start:
            return "."
        elif path.find(start) == 0:
            return path[len(start)+1:]
        else:
            return path

    def _build_ui(self):
        """Creates the UI for this plugin"""
        self._build_notebook_tab()

    def _remove_from_notebook(self):
        """Remove the tab for this plugin from the notebook"""
        notebook = self._frame.notebook
        if notebook:
            notebook.DeletePage(notebook.GetPageIndex(self.panel))

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
        profileLabel = wx.StaticText(toolbar, label="Execution Profile:  ")
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
        self.splitter = wx.SplitterWindow(self.panel, wx.ID_ANY, style=wx.SP_LIVE_UPDATE)
        self.splitter.SetMinimumPaneSize(10)
        self._left_panel = wx.Panel(self.splitter)
        self._right_panel = wx.Panel(self.splitter)
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

        self._tree = TestSuiteTreeCtrl(self._left_panel)
        left_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        left_panel_sizer.Add(self._tree, 1, wx.EXPAND)
        self._left_panel.SetSizer(left_panel_sizer)

        self._menubutton = wx.BitmapButton(self._tree, bitmap=getMenuButtonBitmap(),
                                           style=wx.NO_BORDER)
        msizer = wx.BoxSizer(wx.HORIZONTAL)
        msizer.AddStretchSpacer(1)
        msizer.Add(self._menubutton, 0, wx.ALL|wx.ALIGN_RIGHT)

        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.header_panel.SetSizer(header_sizer)

        self._tree.Bind(wx.EVT_PAINT, self.OnTreePaint)
        self._tree.Bind(wx.EVT_SIZE, self.OnTreeResize)
        self._menubutton.Bind(wx.EVT_BUTTON, self.OnMenuButton)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.local_toolbar, 0, wx.EXPAND)
        sizer.Add(self.configPanel, 0, wx.EXPAND|wx.TOP|wx.RIGHT, 4)
        sizer.Add(wx.StaticLine(self.panel), 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 2)
        sizer.Add(self.header_panel, 0, wx.EXPAND|wx.RIGHT, 10)
        sizer.Add(self.splitter,   1, wx.EXPAND|wx.RIGHT, 8)
        panel.SetSizer(sizer)

        self.splitter.SplitVertically(self._left_panel, self._right_panel, 200)
        # I don't know why but the sash position is being ignored; setting
        # it via CallAfter seems to work
        wx.CallAfter(self._set_splitter_size, self.sash_position)

        self._process_timer = wx.Timer(self.panel)

        self.splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnSplitterSashChanged)
        self.panel.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

        # whitespace added to label just so label isn't so tiny
        self.add_tab(panel, "Run    ", allow_closing=False)

        self._tree_menu = wx.Menu()
        select_all = self._tree_menu.Append(wx.ID_ANY, "Select All")
        select_failed = self._tree_menu.Append(wx.ID_ANY, "Select Only Failed Tests")
        deselect_all = self._tree_menu.Append(wx.ID_ANY, "Deselect All")
        self._tree_menu.AppendSeparator()
        select_children = self._tree_menu.Append(wx.ID_ANY, "Select All Children")
        deselect_children = self._tree_menu.Append(wx.ID_ANY, "Deselect All Children")
        self._tree_menu.AppendSeparator()
        expand_all = self._tree_menu.Append(wx.ID_ANY, "Show All Test Cases")
        collapse_all = self._tree_menu.Append(wx.ID_ANY, "Hide All Test Cases")

        self._tree.Bind(wx.EVT_CONTEXT_MENU, self.OnShowPopup)
        self._tree.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self._tree.Bind(wx.EVT_MENU, self.OnSelectAll, select_all)
        self._tree.Bind(wx.EVT_MENU, self.OnSelectOnlyFailed, select_failed)
        self._tree.Bind(wx.EVT_MENU, self.OnDeselectAll, deselect_all)
        self._tree.Bind(wx.EVT_MENU, self.OnExpandAll, expand_all)
        self._tree.Bind(wx.EVT_MENU, self.OnCollapseAll, collapse_all)
        self._tree.Bind(wx.EVT_MENU, self.OnSelectChildren, select_children)
        self._tree.Bind(wx.EVT_MENU, self.OnDeselectChildren, deselect_children)

    def OnSelectAll(self, event):
        '''Called when the user chooses "Select All" from the menu'''
        self._tree.SelectAll()

    def OnSelectOnlyFailed(self, event):
        '''Called when the user chooses "Select All Failed" from the menu'''
        self._tree.SelectAllFailed()

    def OnDeselectAll(self, event):
        '''Called when the user chooses "Deselect All" from the menu'''
        self._tree.DeselectAll()

    def OnExpandAll(self, event):
        '''Called when the user chooses "Expand All" from the menu'''
        self._tree.ExpandAll()

    def OnCollapseAll(self, event):
        '''Called when the user chooses "Collapse All" from the menu'''
        self._tree.CollapseAll()
    
    def OnSelectChildren(self, event):
        '''Called when the user chooses "Select All Children" from the menu'''
        self._tree.SelectChildren()

    def OnDeselectChildren(self, event):
        '''Called when the user chooses "Deselect All Children" from the menu'''
        self._tree.DeselectChildren()

    def OnShowPopup(self, event):
        '''Show the context-sensitive menu'''
        pos = event.GetPosition()
        pos = self._tree.ScreenToClient(pos)
        self._tree.PopupMenu(self._tree_menu, pos)

    def _reposition_menubutton(self):
        '''Redraw the menubutton

        This is necessary because wxPython doesn't support relative
        placement (ie: place this in the upper right corner of the
        tree)
        '''
        (menubutton_width, _) = self._menubutton.GetSize()
        (_, vh)  = self._tree.GetVirtualSize()
        (_, ch) = self._tree.GetClientSize()
        # N.B. add a little extra offset for margins/borderwidths 
        offset = menubutton_width + 4
        if (ch != vh):
            # scrollbar is visible
            scrollbar_width = wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
            offset += scrollbar_width
        (w,_) = self._tree.GetSize()
        self._menubutton.SetPosition((w-offset, 0))

    def _set_splitter_size(self, size):
        self.splitter.SetSashPosition(size)

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
            self._tree.running_test(longname)
        if event == 'start_suite':
            _, attrs = args
            longname = attrs['longname']
            self._tree.running_suite(longname)
        if event == 'end_test':
            _, attrs = args
            longname = attrs['longname']
            if attrs['status'] == 'PASS':
                self._tree.test_passed(longname)
                self._progress_bar.Pass()
            else:
                self._tree.test_failed(longname)
                self._progress_bar.Fail()
        if event == 'end_suite':
            _, attrs = args
            longname = attrs['longname']
            if attrs['status'] == 'PASS':
                self._tree.suite_passed(longname)
            else:
                self._tree.suite_failed(longname)
        if event == 'report_file':
            self._report_file = args[0]
            self.local_toolbar.EnableTool(ID_SHOW_REPORT, True)

        if event == 'log_file':
            self._log_file = args[0]
            self.local_toolbar.EnableTool(ID_SHOW_LOG, True)

        return

    def _set_state(self, state):
        if state == "running":
            self._run_action.disable()
            self._stop_action.enable()
            self.local_toolbar.EnableTool(ID_RUN, False)
            self.local_toolbar.EnableTool(ID_STOP, True)
            self._running = True
        else:
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
        self._label = wx.StaticText(self)
        self._sizer.Add(self._label, 1, wx.EXPAND|wx.LEFT, 10)
        self._sizer.Add(self._gauge, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        self._sizer.Layout()
        self.SetSizer(self._sizer)
        self._gauge.Hide()
        self._default_colour = parent.GetBackgroundColour()

        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

        self._pass = 0
        self._fail = 0
        self._start = None

    def OnTimer(self, event):
        '''A handler for timer events; it updates the statusbar'''
        self._gauge.Show()
        self._gauge.Pulse()
        self._update_message()

    def Start(self):
        '''Signals the start of a test run; initialize progressbar.'''
        self._pass = 0
        self._fail = 0
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
        self._label.SetLabel(message)
        if self._fail > 0:
            self.SetBackgroundColour("#FF8E8E")
        elif self._pass > 0:
            self.SetBackgroundColour("#9FCC9F")


# The following two classes implement a small line-buffered socket
# server. It is designed to run in a separate thread, read data
# from the given port and update the UI -- hopefully all in a 
# thread-safe manner.
class RideListenerServer(SocketServer.TCPServer):
    """Implements a simple line-buffered socket server"""
    allow_reuse_address = True
    def __init__(self, server_address, RequestHandlerClass, callback):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
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

