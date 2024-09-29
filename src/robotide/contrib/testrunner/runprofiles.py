# Copyright 2010 Orbitz WorldWide
#
# Ammended by Helio Guilherme <helioxentric@gmail.com>
# Copyright 2011-2015 Nokia Networks
# Copyright 2016-     Robot Framework Foundation
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

"""runProfiles.py

This module contains profiles for running robot tests via the
runnerPlugin.

Each class that is a subclass as BaseProfile will appear in a
drop-down list within the plugin. The chosen profile will be used to
build up a command that will be passed in the tests to run as well as
any additional arguments.
"""

import builtins
import os
import re
import time
import wx

from robotide.publish.messages import RideLogMessage
from robotide.context import IS_WINDOWS
from robotide.contrib.testrunner.usages import USAGE
from robotide.lib.robot.utils import format_time
from robotide.robotapi import DataError, Information
from robotide.utils import ArgumentParser
from robotide.widgets import ButtonWithHandler, Label, RIDEDialog
from sys import getfilesystemencoding
from wx.lib.filebrowsebutton import FileBrowseButton

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

OUTPUT_ENCODING = getfilesystemencoding()


class BaseProfile(object):
    """Base class for all test runner profiles

    At a minimum each profile must set the name attribute, which is
    how the profile will appear in the dropdown list.

    In case some settings are needed, provide default_settings class attribute
    with default values.

    This class (BaseProfile) will _not_ appear as one of the choices.
    Think of it as an abstract class, if Python 2.5 had such a thing.
    """

    # this will be set to the plugin instance at runtime
    plugin = None
    default_settings = {}

    def __init__(self, plugin):
        """plugin is required so that the profiles can save their settings"""
        self.plugin = plugin
        self._panel = None

    def get_toolbar(self, parent):
        """Returns a panel with toolbar controls for this profile"""
        if self._panel is None:
            self._panel = wx.Panel(parent, wx.ID_ANY)
        return self.panel

    def enable_toolbar(self):
        if self._panel is None:
            return
        self._panel.Enable()

    def disable_toolbar(self):
        if self._panel is None:
            return
        self._panel.Enable(False)

    def delete_pressed(self):
        """Handle delete key pressing"""
        pass

    def get_command(self):
        """Returns a command for this profile"""
        return 'robot'

    def get_command_args(self):
        """Return a list of command arguments unique to this profile.

        Returned arguments are in format accepted by Robot Framework's argument
        file.
        """
        return []

    def get_settings(self):
        """Return a list of settings unique to this profile.

        Returned settings can be used when running tests.
        """
        return []

    def set_setting(self, name, value):
        """Sets a plugin setting

        setting is automatically prefixed with profile's name, and it can be
        accessed with direct attribute access. See also __getattr__.
        """
        self.plugin.save_setting(self._get_setting_name(name), value, delay=2)

    def format_error(self, error, returncode):
        return error, self._create_error_log_message(error, returncode)

    def _create_error_log_message(self, error, returncode):
        _ = error, returncode
        return None

    def __getattr__(self, name):
        """Provides attribute access to profile's settings

        If for example default_settings = {'setting1' = ""} is defined
        then setting1 value can be used like self.setting1
        set_setting is used to store the value.
        """
        try:
            return getattr(self.plugin, self._get_setting_name(name))
        except AttributeError:
            try:
                return getattr(self.plugin, name)
            except AttributeError:
                if name in self.default_settings:
                    return self.default_settings[name]
                raise

    def _get_setting_name(self, name):
        """Adds profile's name to the setting."""
        return "%s_%s" % (self.name.replace(' ', '_'), name)


RF_INSTALLATION_NOT_FOUND = """Robot Framework installation not found.<br>
To run tests, you need to install Robot Framework separately.<br>
See <a href="https://robotframework.org/">https://robotframework.org/</a> for
installation instructions.
"""


class PybotProfile(BaseProfile):
    """A runner profile which uses robot

    It is assumed that robot is on the path
    """
    _quotes_re = re.compile('(.*)(\".*\")(.*)?')

    name = "robot"
    default_settings = {"arguments": "",
                        "output_directory": "",
                        "include_tags": "",
                        "exclude_tags": "",
                        "are_log_names_with_suite_name": False,
                        "are_log_names_with_timestamp": False,
                        "are_saving_logs": False,
                        "apply_include_tags": False,
                        "apply_exclude_tags": False}

    def __init__(self, plugin):
        BaseProfile.__init__(self, plugin)
        self._defined_arguments = self.arguments
        self._toolbar = None
        self._mysettings = None

    def get_toolbar(self, parent):
        if self._toolbar is None:
            self._toolbar = wx.Panel(parent, wx.ID_ANY)
            self._mysettings = RIDEDialog(parent=self._toolbar)
            self._toolbar.SetBackgroundColour(self._mysettings.color_background)
            self._toolbar.SetForegroundColour(self._mysettings.color_foreground)
            sizer = wx.BoxSizer(wx.VERTICAL)
            for item in self.get_toolbar_items(self._toolbar):
                sizer.Add(item, 0, wx.EXPAND)
            self._toolbar.SetSizer(sizer)
        return self._toolbar

    def get_toolbar_items(self, parent):
        return [self._get_arguments_panel(parent),
                self._get_tags_panel(parent),
                self._get_log_options_panel(parent)]

    def enable_toolbar(self):
        if self._toolbar is None:
            return
        self._enable_toolbar()

    def disable_toolbar(self):
        if self._toolbar is None:
            return
        self._enable_toolbar(False)

    def _enable_toolbar(self, enable=True):
        for panel in self._toolbar.GetChildren():
            if isinstance(panel, wx.CollapsiblePane):
                panel = panel.GetPane()
            panel.Enable(enable)

    def delete_pressed(self):
        focused = wx.Window.FindFocus()
        if focused not in [self._arguments, self._include_tags,
                           self._exclude_tags]:
            return
        start, end = focused.GetSelection()
        focused.Remove(start, max(end, start + 1))

    def get_command(self):
        from subprocess import call
        from tempfile import TemporaryFile
        try:
            with TemporaryFile(mode="at") as out:
                result = call(["robot", "--version"], stdout=out)
            if result == 251:
                return "robot"

            with TemporaryFile(mode="at") as out:
                result = call(["robot.bat" if os.name == "nt" else "robot",
                               "--version"], stdout=out)
            if result == 251:
                return "robot.bat" if os.name == "nt" else "robot"
        except OSError:
            try:
                with TemporaryFile(mode="at") as out:
                    result = call(["pybot.bat" if os.name == "nt" else "pybot",
                                   "--version"], stdout=out)
                if result == 251:
                    return "pybot.bat" if os.name == "nt" else "pybot"
            except OSError:
                result = "no pybot"
        return result

    def get_command_args(self):
        args = self._get_arguments()
        if self.output_directory and \
                '--outputdir' not in args and \
                '-d' not in args:
            args.extend(['-d', os.path.abspath(self.output_directory)])

        log_name_format = '%s'
        if self.are_log_names_with_suite_name:
            log_name_format = f'{self.plugin.model.suite.name}-%s'
            if '--log' not in args and '-l' not in args:
                args.extend(['-l', log_name_format % 'Log.html'])
            if '--report' not in args and '-r' not in args:
                args.extend(['-r', log_name_format % 'Report.html'])
            if '--output' not in args and '-o' not in args:
                args.extend(['-o', log_name_format % 'Output.xml'])

        if self.are_saving_logs and \
                '--debugfile' not in args and \
                '-b' not in args:
            args.extend(['-b', log_name_format % 'Message.log'])

        if self.are_log_names_with_timestamp and \
                '--timestampoutputs' not in args and \
                '-T' not in args:
            args.append('-T')

        if self.apply_include_tags and self.include_tags:
            for include in self._get_tags_from_string(self.include_tags):
                args.append('--include=%s' % include)

        if self.apply_exclude_tags and self.exclude_tags:
            for exclude in self._get_tags_from_string(self.exclude_tags):
                args.append('--exclude=%s' % exclude)
        return args

    def _get_arguments(self):
        if IS_WINDOWS:
            self._parse_windows_command()
        else:
            self._parse_posix_command()
        return self._save_filenames()

    def _save_filenames(self):
        args = self._defined_arguments.replace('\\"', '"')
        res = self._quotes_re.match(args)
        if not res:
            return args.strip().strip().split()
        clean = []
        # DEBUG: example args
        # --xunit "another output file.xml" --variablefile "a test file for variables.py" -v abc:new
        # --debugfile "debug file.log"
        # print(f"DEBUG: Run Profiles _save_filenames res.groups {res.groups()}")
        for gr in res.groups():
            line = []
            if gr is not None and gr != '':
                second_m = re.split('"', gr)
                # print(f"DEBUG: Run Profiles _save_filenames second_m = {second_m}")
                m = len(second_m)
                if m > 2:  # the middle element is the content
                    m = len(second_m)
                    for idx in range(0, m):
                        if second_m[idx]:
                            if idx % 2 == 0:
                                line.extend(second_m[idx].strip().strip().split())
                            elif idx % 2 != 0:
                                line.append(f"{second_m[idx]}")
                else:
                    for idx in range(0, m):
                        if second_m[idx]:
                            line.extend(second_m[idx].strip().strip().split())
            clean.extend(line)
        # Fix variables
        # print(f"DEBUG: Run Profiles  _save_filenames DEFORE FIX VARIABLES clean= {clean}")
        for idx, value in enumerate(clean):
            if value[-1] == ':' and idx + 1 < len(clean):
                clean[idx] = ''.join([value, clean[idx+1]])
                clean.pop(idx+1)
        # print(f"DEBUG: Run Profiles  _save_filenames returnin clean= {clean}")
        return clean

    def _parse_windows_command(self):
        from subprocess import Popen, PIPE
        try:
            p = Popen(['echo', self.arguments], stdin=PIPE, stdout=PIPE,
                      stderr=PIPE, shell=True)
            output, _ = p.communicate()
            from ctypes import cdll

            code_page = cdll.kernel32.GetConsoleCP()
            if code_page == 0:
                os_encoding = os.getenv('RIDE_ENCODING', OUTPUT_ENCODING)
            else:
                os_encoding = 'cp' + str(code_page)
            try:
                output = output.decode(os_encoding)
            except UnicodeDecodeError:
                wx.MessageBox(f"An UnicodeDecodeError occurred when processing the Arguments."
                              f" The encoding used was '{os_encoding}'. You may try to define the environment variable"
                              f" RIDE_ENCODING with a proper value. Other possibility, is to replace 'pythonw.exe' by "
                              f"'python.exe' in the Desktop Shortcut.", "UnicodeDecodeError")
            output = str(output).lstrip("b\'").lstrip('"').replace('\\r\\n', '').replace('\'', '').\
                replace('\\""', '\"').strip()
            # print(f"DEBUG: run_profiles _parse_windows_command: output ={output}")
            even = True
            counter = 0
            for idx in range(0, len(output)):
                if output[idx] == '"':
                    counter += 1
                    even = counter % 2 == 0
                # print(f"DEBUG: run_profiles loop({idx} counter:{counter}")
            self._defined_arguments = output.replace('\'', '')\
                .replace('\\\\', '\\').replace('\\r\\n', '')
            if not even:
                self._defined_arguments = self._defined_arguments.rstrip('"')
        except IOError:
            pass

    def _parse_posix_command(self):
        # print(f"DEBUG: run_profiles _parse_posix_command: ENTER  self.arguments={self.arguments}")
        from subprocess import Popen, PIPE
        try:
            p = Popen(['echo ' + self.arguments.replace('"', '\\"')], stdin=PIPE, stdout=PIPE,
                      stderr=PIPE, shell=True)
            output, _ = p.communicate()
            # print(f"DEBUG: run_profiles _parse_posix_command: RAW output ={output}")
            output = str(output).lstrip("b\'").replace('\\n', '').rstrip("\'").strip()
            # print(f"DEBUG: run_profiles _parse_posix_command: output ={output}")
            even = True
            counter = 0
            for idx in range(0, len(output)):
                if output[idx] == '"':
                    counter += 1
                    even = counter % 2 == 0
                # print(f"DEBUG: run_profiles loop({idx} counter:{counter}")
            self._defined_arguments = output.replace('\'', '')\
                .replace('\\\\', '\\').replace('\\n', '')
            if not even:
                self._defined_arguments = self._defined_arguments.rstrip('"')
        except IOError:
            pass

    @staticmethod
    def _get_tags_from_string(tag_string):
        tags = []
        for tag in tag_string.split(","):
            tag = tag.strip().replace(' ', '')
            if len(tag) > 0:
                tags.append(tag)
        return tags

    def get_settings(self):
        settings = []
        if self.are_saving_logs:
            name = 'Console.txt'
            if self.are_log_names_with_timestamp:
                start_timestamp = format_time(time.time(), '', '-', '')
                base, ext = os.path.splitext(name)
                base = f'{base}-{start_timestamp}'
                name = base + ext

            if self.are_log_names_with_suite_name:
                name = f'{self.plugin.model.suite.name}-{name}'
            settings.extend(['console_log_name', name])
        return settings

    def _create_error_log_message(self, error, returncode):
        # bash and zsh use return code 127 and the text `command not found`
        # In Windows, the error is `The system cannot file the file specified`
        if b'not found' in error \
                or returncode == 127 or \
                b'system cannot find the file specified' in error:
            return RideLogMessage(RF_INSTALLATION_NOT_FOUND, notify_user=True)
        return None

    def _get_log_options_panel(self, parent):
        collapsible_pane = wx.CollapsiblePane(
            parent, wx.ID_ANY, _('Log options'),
            style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        collapsible_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
                              self.on_collapsible_pane_changed,
                              collapsible_pane)
        pane = collapsible_pane.GetPane()
        pane.SetThemeEnabled(False)
        pane.SetBackgroundColour(self._mysettings.color_background)
        pane.SetForegroundColour(self._mysettings.color_foreground)
        label = Label(pane, label=_("Output directory: "))
        label.SetBackgroundColour(self._mysettings.color_background)
        label.SetForegroundColour(self._mysettings.color_foreground)
        self._output_directory_text_ctrl = \
            self._create_text_ctrl(pane, self.output_directory,
                                   "removed due unicode_error (delete this)",
                                   self.on_output_directory_changed)
        self._output_directory_text_ctrl.SetBackgroundColour(self._mysettings.color_secondary_background)
        self._output_directory_text_ctrl.SetForegroundColour(self._mysettings.color_secondary_foreground)
        button = ButtonWithHandler(pane, "...", handler=self._handle_select_directory)
        button.SetBackgroundColour(self._mysettings.color_secondary_background)
        button.SetForegroundColour(self._mysettings.color_secondary_foreground)
        horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        horizontal_sizer.Add(label, 0,
                             wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        horizontal_sizer.Add(self._output_directory_text_ctrl, 1, wx.EXPAND)
        horizontal_sizer.Add(button, 0, wx.LEFT | wx.RIGHT, 10)

        suite_name_outputs_cb = self._create_checkbox(
            pane, self.are_log_names_with_suite_name,
            _("Add suite name to log names"), self.on_suite_name_outputs_check_box)
        timestamp_outputs_cb = self._create_checkbox(
            pane, self.are_log_names_with_timestamp,
            _("Add timestamp to log names"), self.on_timestamp_outputs_checkbox)
        save_logs_cb = self._create_checkbox(
            pane, self.are_saving_logs,
            _("Save Console and Message logs"), self.on_save_logs_checkbox)

        vertical_sizer = wx.BoxSizer(wx.VERTICAL)
        vertical_sizer.Add(horizontal_sizer, 0, wx.EXPAND)
        vertical_sizer.Add(suite_name_outputs_cb, 0, wx.LEFT | wx.TOP, 10)
        vertical_sizer.Add(timestamp_outputs_cb, 0, wx.LEFT | wx.TOP, 10)
        vertical_sizer.Add(save_logs_cb, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 10)
        pane.SetSizer(vertical_sizer)
        return collapsible_pane

    def on_output_directory_changed(self, evt):
        _ = evt
        value = self._output_directory_text_ctrl.GetValue()
        self.set_setting("output_directory", value)

    def _handle_select_directory(self, event):
        __ = event
        path = self._output_directory_text_ctrl.GetValue()
        dlg = wx.DirDialog(None, _("Select Logs Directory"),
                           path, wx.DD_DEFAULT_STYLE)
        dlg.SetBackgroundColour(self._mysettings.color_background)
        dlg.SetForegroundColour(self._mysettings.color_foreground)
        for item in dlg.GetChildren():  # DEBUG This is not working
            item.SetBackgroundColour(self._mysettings.color_secondary_background)
            item.SetForegroundColour(self._mysettings.color_secondary_foreground)
        if dlg.ShowModal() == wx.ID_OK and dlg.Path:
            self._output_directory_text_ctrl.SetValue(dlg.Path)
        dlg.Destroy()

    def on_suite_name_outputs_check_box(self, evt):
        self.set_setting("are_log_names_with_suite_name", evt.IsChecked())

    def on_timestamp_outputs_checkbox(self, evt):
        self.set_setting("are_log_names_with_timestamp", evt.IsChecked())

    def on_save_logs_checkbox(self, evt):
        self.set_setting("are_saving_logs", evt.IsChecked())

    def _get_arguments_panel(self, parent):
        collapsible_pane = wx.CollapsiblePane(
            parent, wx.ID_ANY, _('Arguments'),
            style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        collapsible_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
                              self.on_collapsible_pane_changed,
                              collapsible_pane)
        pane = collapsible_pane.GetPane()
        pane.SetThemeEnabled(False)
        pane.SetBackgroundColour(self._mysettings.color_background)
        pane.SetForegroundColour(self._mysettings.color_foreground)
        self._args_text_ctrl = \
            self._create_text_ctrl(pane, self.arguments,
                                   "removed due unicode_error (delete this)",
                                   self.on_arguments_changed)
        self._args_text_ctrl.SetToolTip(_("Arguments for the test run. "
                                        "Arguments are space separated list."))
        self._args_text_ctrl.SetBackgroundColour(self._mysettings.color_secondary_background)
        self._args_text_ctrl.SetForegroundColour(self._mysettings.color_secondary_foreground)
        horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        horizontal_sizer.Add(self._args_text_ctrl, 1,
                             wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        pane.SetSizer(horizontal_sizer)
        self._validate_arguments(self.arguments or u'')
        return collapsible_pane

    def on_arguments_changed(self, evt):
        _ = evt
        args = self._args_text_ctrl.GetValue()
        self._validate_arguments(args or u'')
        self.set_setting("arguments", args)
        self._defined_arguments = args

    def _validate_arguments(self, args):
        invalid_message = self._get_invalid_message(args)
        self._args_text_ctrl.SetBackgroundColour(
            'red' if invalid_message else self._mysettings.color_secondary_background)
        self._args_text_ctrl.SetForegroundColour(
            'white' if invalid_message else self._mysettings.color_secondary_foreground)
        if not bool(invalid_message):
            invalid_message = _("Arguments for the test run. Arguments are space separated list.")
        self._args_text_ctrl.SetToolTip(invalid_message)

    @staticmethod
    def _get_invalid_message(args):
        invalid = False
        if not args:
            return None
        try:
            clean_args = args.split("`")  # Shell commands
            # print(f"DEBUG: run_profiles _get_invalid_message ENTER clean_args= {clean_args}")
            for idx, item in enumerate(clean_args):
                clean_args[idx] = item.strip()
                if clean_args[idx] and clean_args[idx][0] != '-':  # Not option, then is argument
                    clean_args[idx] = 'arg'
            args = " ".join(clean_args)
            # print(f"DEBUG: run_profiles _get_invalid_message: Check invalid args={args}")
            __, invalid = ArgumentParser(USAGE).parse_args(args)  # DEBUG .split())
        except Information:
            return _('Does not execute - help or version option given')
        except (DataError, Exception) as e:
            if e.message:
                return e.message
        if bool(invalid):
            return f'{_("Unknown option(s):")} {invalid}'
        return None

    def _get_tags_panel(self, parent):
        """Create a panel to input include/exclude tags"""
        collapsible_pane = wx.CollapsiblePane(
            parent, wx.ID_ANY, _('Tests filters'),
            style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        collapsible_pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
                              self.on_collapsible_pane_changed,
                              collapsible_pane)
        pane = collapsible_pane.GetPane()
        pane.SetThemeEnabled(False)
        pane.SetBackgroundColour(self._mysettings.color_background)
        pane.SetForegroundColour(self._mysettings.color_foreground)
        include_cb = self._create_checkbox(pane, self.apply_include_tags,
                                           _("Only run tests with these tags:"),
                                           self.on_include_checkbox)
        exclude_cb = self._create_checkbox(pane, self.apply_exclude_tags,
                                           _("Skip tests with these tags:"),
                                           self.on_exclude_checkbox)
        self._include_tags_text_ctrl = \
            self._create_text_ctrl(pane, self.include_tags, "unicode_error",
                                   self.on_include_tags_changed,
                                   self.apply_include_tags)
        self._exclude_tags_text_ctrl = \
            self._create_text_ctrl(pane, self.exclude_tags, "unicode error",
                                   self.on_exclude_tags_changed,
                                   self.apply_exclude_tags)
        self._include_tags_text_ctrl.SetBackgroundColour(self._mysettings.color_secondary_background)
        self._include_tags_text_ctrl.SetForegroundColour(self._mysettings.color_secondary_foreground)
        self._exclude_tags_text_ctrl.SetBackgroundColour(self._mysettings.color_secondary_background)
        self._exclude_tags_text_ctrl.SetForegroundColour(self._mysettings.color_secondary_foreground)
        horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        horizontal_sizer.Add(include_cb, 0, wx.ALIGN_CENTER_VERTICAL)
        horizontal_sizer.Add(self._include_tags_text_ctrl, 1, wx.EXPAND)
        horizontal_sizer.Add(exclude_cb, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        horizontal_sizer.Add(self._exclude_tags_text_ctrl, 1, wx.EXPAND)
        # Set Left, Right and Bottom content margins
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(horizontal_sizer, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        pane.SetSizer(sizer)

        return collapsible_pane

    def on_collapsible_pane_changed(self, evt=None):
        _ = evt
        parent = self._toolbar.GetParent().GetParent()
        parent.Layout()

    def on_include_checkbox(self, evt):
        self.set_setting("apply_include_tags", evt.IsChecked())
        self._include_tags_text_ctrl.Enable(evt.IsChecked())

    def on_exclude_checkbox(self, evt):
        self.set_setting("apply_exclude_tags", evt.IsChecked())
        self._exclude_tags_text_ctrl.Enable(evt.IsChecked())

    def on_include_tags_changed(self, evt):
        _ = evt
        self.set_setting("include_tags", self._include_tags_text_ctrl.GetValue())

    def on_exclude_tags_changed(self, evt):
        _ = evt
        self.set_setting("exclude_tags", self._exclude_tags_text_ctrl.GetValue())

    def _create_checkbox(self, parent, value, title, handler):
        checkbox = wx.CheckBox(parent, wx.ID_ANY, title)
        checkbox.SetValue(value)
        checkbox.SetBackgroundColour(self._mysettings.color_background)
        checkbox.SetForegroundColour(self._mysettings.color_foreground)
        parent.Bind(wx.EVT_CHECKBOX, handler, checkbox)
        return checkbox

    def _create_text_ctrl(self, parent, value, value_for_error,
                          text_change_handler, enable=True):
        try:
            text_ctrl = wx.TextCtrl(parent, wx.ID_ANY, value=value)
        except UnicodeError:
            text_ctrl = wx.TextCtrl(parent, wx.ID_ANY, value=value_for_error)
        text_ctrl.SetBackgroundColour(self._mysettings.color_background)
        text_ctrl.SetForegroundColour(self._mysettings.color_foreground)
        text_ctrl.Bind(wx.EVT_TEXT, text_change_handler)
        text_ctrl.Enable(enable)
        return text_ctrl


class CustomScriptProfile(PybotProfile):
    """A runner profile which uses script given by the user"""

    name = "custom script"
    default_settings = dict(PybotProfile.default_settings, runner_script="")

    def get_command(self):
        # strip the starting and ending spaces to ensure
        # /bin/sh finding the executable file
        return self.runner_script.strip()

    def get_cwd(self):
        return os.path.dirname(self.runner_script)

    def get_toolbar_items(self, parent):
        return [self._get_run_script_panel(parent),
                self._get_arguments_panel(parent),
                self._get_tags_panel(parent),
                self._get_log_options_panel(parent)]

    def _validate_arguments(self, args):
        # Can't say anything about custom script argument validity
        pass

    def _create_error_log_message(self, error, returncode):
        return None

    def _get_run_script_panel(self, parent):
        panel = wx.Panel(parent, wx.ID_ANY)
        self._script_ctrl = FileBrowseButton(
            panel, labelText=_("Script to run tests:"), size=(-1, -1),
            fileMask="*", changeCallback=self.on_custom_script_changed)
        self._script_ctrl.SetValue(self.runner_script)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._script_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        panel.SetSizerAndFit(sizer)
        return panel

    def on_custom_script_changed(self, evt):
        _ = evt
        self.set_setting("runner_script", self._script_ctrl.GetValue())
