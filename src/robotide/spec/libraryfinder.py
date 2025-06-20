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

import builtins
import sys

import wx
from dataclasses import dataclass

from ..action import ActionInfo
from ..editor.editordialogs import LibraryFinderDialog
from ..pluginapi import Plugin
from ..publish import PUBLISHER, RideExecuteLibraryInstall, RideOpenLibraryDocumentation

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class LibraryFinderPlugin(Plugin):
    __doc__ = _("""Install missing libraries and open documentation.

    You can edit settings.cfg to add URL for documentation and command to install.
    You can right-click on a Library name, and Open Documentation or Install Library.
    From Tools->Library Finder... or Help->Open Library Documentation... you will have
    a dialog to fill the command to install or the URL for the documentation.
    """)

    HEADER = _('Library Finder...')
    LIBDOC = _('Open Library Documentation...')

    def enable(self):
        self.register_action(ActionInfo(_('Tools'), self.HEADER, self.execute_library_install,
                                        doc=_('Prepare Info to Install Libraries')))
        self.register_action(ActionInfo(_('Help'), self.LIBDOC, self.open_library_documentation,
                                        doc=_('Prepare Info to Open Documentation of Libraries')))
        PUBLISHER.subscribe(self._ps_on_execute_library_install, RideExecuteLibraryInstall)
        PUBLISHER.subscribe(self._ps_on_open_library_documentation, RideOpenLibraryDocumentation)

    def disable(self):
        self.unsubscribe_all()
        self.unregister_actions()

    def _ps_on_execute_library_install(self, message):
        self.execute_library_install(message)

    def _ps_on_open_library_documentation(self, message):
        self.open_library_documentation(message)

    def open_library_documentation(self, message):
        library_name = None
        if isinstance(message, RideOpenLibraryDocumentation):
            library_name = message.item
            doc_url = self.find_documentation_url(library_name)
            if doc_url:
                # Call doc_url execution
                wx.LaunchDefaultBrowser(doc_url)
                return None
        # Call input dialog for doc_url
        value = self.on_library_form(name=None if not library_name else library_name)
        if isinstance(value, list):
            doc_url = value[1] or None
            if not doc_url:
                doc_url = self.find_documentation_url(value[0])
                dlg = wx.TextEntryDialog(self.frame,
                                         message=f"Enter the URL for the keywords documentation of {value[0]}",
                                         value=doc_url, caption="URL for Library Documentation")
                result = dlg.ShowModal()
                if result == wx.ID_OK:
                    doc_url = dlg.GetValue()
                dlg.Destroy()
                if result != wx.ID_OK:
                    return None
            if doc_url:
                wx.LaunchDefaultBrowser(doc_url)
                if self._is_std_library(value[0]):
                    return None
                plugin_section = self.global_settings['Plugins'][self.name]
                plugin_section.add_section(value[0])
                self.global_settings['Plugins'][self.name][value[0]]['documentation'] = doc_url
                if value[2]:
                    command = value[2]
                    if isinstance(command, str):
                        lst_command = command.split('|')
                    else:
                        lst_command = command
                    self.global_settings['Plugins'][self.name][value[0]]['command'] = lst_command
        return None

    def on_library_form(self, name):
        doc_url = command = ''
        if name:
            doc_url = self.find_documentation_url(name)
            command = self.find_install_command(name)
        item = RunnerCommand(name=name, command=command, documentation=doc_url)
        dlg = LibraryFinderDialog(self.get_selected_item(), item=item, plugin=self, title=_('Library Finder'))
        result = dlg.ShowModal()
        wx.CallAfter(dlg.Destroy)
        if result == wx.ID_OK:
            return dlg.get_value()
        else:
            return -1

    def execute_library_install(self, message):
        library_name = None
        if isinstance(message, RideExecuteLibraryInstall):
            library_name = message.item
        value = self.on_library_form(name=library_name)
        if value == -1:
            return None
        if isinstance(value, list):
            library_name = value[0] or None
            try:
                command = value[2]
            except IndexError:
                command = None
            if library_name:
                if self._is_std_library(library_name):
                    return None
                if not command:
                    command = self.find_install_command(library_name)
                if command and isinstance(command, list):
                    command = " | ".join(command).strip(" |")
                dlg = wx.TextEntryDialog(self.frame, message=f"Enter command to install {value[0]}",
                                         value=command or "%executable -m pip install -U ",
                                         caption="Command to Install Library")
                result = dlg.ShowModal()
                if result == wx.ID_OK:
                    command = dlg.GetValue()
                dlg.Destroy()
                if result != wx.ID_OK:
                    return False
            else:
                return False
            if isinstance(command, str):
                lst_command = command.split('|')
            else:
                lst_command = command
            if lst_command:
                plugin_section = self.global_settings['Plugins'][self.name]
                plugin_section.add_section(library_name)
                if value[1]:
                    self.global_settings['Plugins'][self.name][library_name]['documentation'] = value[1]
                self.global_settings['Plugins'][self.name][library_name]['command'] = lst_command

        command = self.find_install_command(library_name)
        if command:
            # Call command execution
            self.statusbar_message(f"Library Installer: Starting installing {library_name}", 5000)
            result = self.run_install(library_name, self.parse_command(command))
            if result:
                self._execute_namespace_update()
                self.notebook.Refresh()
                self.statusbar_message(f"Library Installer: Success installing {library_name}", 5000)
            else:
                self.statusbar_message(f"Library Installer: Failed to install {library_name}", 5000)
        return None

    def find_install_command(self, name):
        if not name:
            return []
        try:
            plug = self.global_settings['Plugins'][self.name][name]
        except Exception:
            plug = None
        if plug:
            try:
                return plug['command']
            except Exception:
                pass
        return []

    def parse_command(self, command: list) -> list:
        try:
            executable = self.global_settings['executable']
        except Exception:
            executable = sys.executable
        parsed = []
        for cmd in command:
            parsed.append(cmd.replace('%executable', executable))
        return parsed

    def run_install(self, library_name, command):
        if not library_name or not command:
            return False
        from ..run import ui
        result = -1
        for cmd in command:  # TODO: Run commands sequentially, or wait for completion in order
            config = RunnerCommand(f'Installing {library_name}', cmd, f'Run command: {cmd}')
            result = ui.Runner(config, self.notebook).run()
        if result == -1:
            return False
        return True

    def find_documentation_url(self, name):
        try:
            plug = self.global_settings['Plugins'][self.name][name]
        except Exception:
            plug = None
        if plug:
            try:
                return plug['documentation']
            except Exception:
                pass
        if self._is_std_library(name):
            if name == "Remote":
                return "https://github.com/robotframework/RemoteInterface"
            return f"https://robotframework.org/robotframework/latest/libraries/{name}.html"
        return ''

    @staticmethod
    def _is_std_library(name: str) -> bool:
        # Standard Library?
        from robot.libraries import STDLIBS
        std_lib_names = [x for x in STDLIBS]
        return name in std_lib_names

    def _execute_namespace_update(self):
        self.model.update_namespace()


@dataclass
class RunnerCommand:
    def __init__(self, name, command, documentation):
        self.name = name
        self.command = command
        self.documentation = documentation
