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
import os
import shutil
import sys

import wx
from dataclasses import dataclass

from .. import context
from ..action import ActionInfo
from ..editor.editordialogs import LibraryFinderDialog
from ..namespace.cache import LibraryCache
from ..pluginapi import Plugin
from ..publish import PUBLISHER, RideExecuteLibraryInstall, RideRunnerStopped, RideOpenLibraryDocumentation
from ..widgets import RIDEDialog
from .xmlreaders import get_name_from_xml

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class LibraryFinderPlugin(Plugin):
    __doc__ = _("""Install missing libraries and open documentation.

    You can edit settings.cfg to add URL for documentation and command to install. You can right-click and Open
     Documentation or Install Library.
    """)

    HEADER = _('Library Finder...')
    LIBDOC = _('Open Library Documentation...')

    def enable(self):
        self.register_action(ActionInfo(_('Tools'), self.HEADER, self.execute_library_install))
        self.register_action(ActionInfo(_('Help'), self.LIBDOC, self.open_library_documentation))
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
        # print(f"DEBUG: libraryfinder.py LibraryFinderPlugin open_library_documentation message={message}")
        library_name = None
        if isinstance(message, RideOpenLibraryDocumentation):
            library_name = message.item
            doc_url = self.find_documentation_url(library_name)
            if doc_url:
                # Call doc_url execution
                wx.LaunchDefaultBrowser(doc_url)
                return
        # Call input dialog for doc_url
        value = self.on_library_form(name=None if not library_name else library_name)
        if value:
            # print(f"DEBUG: libraryfinder.py LibraryFinderPlugin open_library_documentation ASK for doc_url:"
            #       f" value={value}")
            doc_url = value[1] or None
            if not doc_url:
                dlg = wx.TextEntryDialog(self.frame, message=f"Enter the URL for the keywords documentation of"
                                                             f" {value[0]}", caption="URL for Library Documentation")
                if dlg.ShowModal() == wx.ID_OK:
                    doc_url = dlg.GetValue()
                dlg.Destroy()
            if doc_url:
                wx.LaunchDefaultBrowser(doc_url)
                plugin_section = self.global_settings['Plugins'][self.name]
                plugin_section.add_section(value[0])
                self.global_settings['Plugins'][self.name][value[0]]['documentation'] = doc_url
                if value[2]:
                    self.global_settings['Plugins'][self.name][value[0]]['command'] = [value[2]]

    def on_library_form(self, name):
        value = None
        item = RunnerCommand(name=name, command='', documentation='')
        dlg = LibraryFinderDialog(self.get_selected_item(), item=item, plugin=self, title=_('Library'))
        if dlg.ShowModal() == wx.ID_OK:
            value = dlg.get_value()
        dlg.Destroy()
        return value

    def execute_library_install(self, message):
        # print(f"DEBUG: libraryfinder.py LibraryFinderPlugin execute_library_install message={message}")
        library_name = None
        if isinstance(message, RideExecuteLibraryInstall):
            library_name = message.item
        value = self.on_library_form(name=library_name)
        if value:
            library_name = value[0] or None
            command = value[2] or None
            if not command:
                dlg = wx.TextEntryDialog(self.frame, message=f"Enter command to install {value[0]}",
                                         value="%executable -m pip install -U ",
                                         caption="Command to Install Library")
                if dlg.ShowModal() == wx.ID_OK:
                    command = dlg.GetValue()
                dlg.Destroy()
            if command:
                plugin_section = self.global_settings['Plugins'][self.name]
                plugin_section.add_section(value[0])
                if value[1]:
                    self.global_settings['Plugins'][self.name][value[0]]['documentation'] = value[1]
                self.global_settings['Plugins'][self.name][value[0]]['command'] = [command]

        command = self.find_install_command(library_name)
        if command:
            # Call command execution
            # print(f"DEBUG: libraryfinder.py LibraryFinderPlugin execute_library_install CALL install:"
            #       f" command={command}")
            self.statusbar_message(f"Library Installer: Starting installing {library_name}", 5)
            result = self.run_install(library_name, command)
            if result:
                # print(f"DEBUG: libraryfinder.py LibraryFinderPlugin execute_library_install SUCCESS REFRESHING")
                self._execute_namespace_update()
                self.notebook.Refresh()
                self.statusbar_message(f"Library Installer: Success installing {library_name}", 5)
                return
            else:
                # print(f"DEBUG: libraryfinder.py LibraryFinderPlugin execute_library_install FAILED TO INSTALL")
                self.statusbar_message(f"Library Installer: Failed to install {library_name}", 5)

    def find_install_command(self, name):
        try:
            plug = self.global_settings['Plugins'][self.name][name]
        except Exception:
            plug = None
        if plug:
            # print(f"DEBUG: libraryfinder.py LibrayFinderPlugin find_install_command FOUND name={name} plug={plug}")
            try:
                return self.parse_command(plug['command'])
            except Exception:
                pass
        return False

    def parse_command(self, command: list) -> list:
        try:
            executable = self.global_settings['executable']
        except Exception:
            executable = sys.executable
        # print(f"DEBUG: libraryfinder.py LibraryFinderPlugin parse_command executable={executable}")
        parsed = []
        for cmd in command:
            parsed.append(cmd.replace('%executable', executable))
        return parsed

    def run_install(self, library_name, command):
        from ..run import ui
        result = -1
        for cmd in command:
            config = RunnerCommand(f'Installing {library_name}', cmd, f'Run command: {cmd}')
            result = ui.Runner(config, self.notebook).run()
        if result == -1:
            # print("DEBUG: libraryfinder.py LibraryFinderPlugin run_install FAILED")
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
        # Standard Library?
        from robot.libraries import STDLIBS
        # std_lib_names = wx.App.Get().namespace._lib_cache._default_libraries
        # lib_names = wx.App.Get().namespace.get_all_cached_library_names()
        std_lib_names = [ x for x in STDLIBS]
        if name in std_lib_names:
            if name == "Remote":
                return "https://github.com/robotframework/RemoteInterface"
            return f"https://robotframework.org/robotframework/latest/libraries/{name}.html"
        # print(f"DEBUG: libraryfinder.py LibraryFinderPlugin find_install_command DOC lib_names={std_lib_names}")
        return False

    def _execute_namespace_update(self):
        self.model.update_namespace()


@dataclass
class RunnerCommand:
    def __init__(self, name, command, documentation, comment=None):
        self.name = name
        self.command = command
        self.documentation = documentation
        self.comment = comment if comment else ['']
