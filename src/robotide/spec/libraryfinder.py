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
from ..namespace.cache import LibraryCache
from ..pluginapi import Plugin
from ..publish import PUBLISHER, RideExecuteLibraryInstall, RideRunnerStopped, RideOpenLibraryDocumentation
from ..widgets import RIDEDialog
from .xmlreaders import get_name_from_xml

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class LibraryFinderPlugin(Plugin):

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
        print(f"DEBUG: libraryfinder.py LibraryFinderPlugin open_library_documentation message={message}")
        library_name = None
        if isinstance(message, RideOpenLibraryDocumentation):
            library_name = message.item
            print(f"DEBUG: libraryfinder.py LibraryFinderPlugin open_library_documentation"
                  f" library_name={library_name}")
            doc_url = self.find_documentation_url(library_name)
            if doc_url:
                # Call doc_url execution
                print(f"DEBUG: libraryfinder.py LibraryFinderPlugin open_library_documentation OPEN DOC:"
                      f" doc_url={doc_url}")
                wx.LaunchDefaultBrowser(doc_url)
                return
        # Call input dialog for doc_url
        print(f"DEBUG: libraryfinder.py LibraryFinderPlugin open_library_documentation ASK for doc_url:"
              f" message={message}")

    def execute_library_install(self, message):
        print(f"DEBUG: libraryfinder.py LibraryFinderPlugin execute_library_install message={message}")
        library_name = None
        if isinstance(message, RideExecuteLibraryInstall):
            library_name = message.item
            print(f"DEBUG: libraryfinder.py LibrayFinderPlugin execute_library_install"
                  f" library_name={library_name}")
            command = self.find_install_command(library_name)
            if command:
                # Call command execution
                print(f"DEBUG: libraryfinder.py LibraryFinderPlugin execute_library_install CALL install:"
                      f" command={command}")
                result = self.run_install(library_name, command)
                if result:
                    print(f"DEBUG: libraryfinder.py LibraryFinderPlugin execute_library_install SUCCESS REFRESHING")
                    self._execute_namespace_update()
                    self.notebook.Refresh()
                    return
                else:
                    print(f"DEBUG: libraryfinder.py LibraryFinderPlugin execute_library_install FAILED TO INSTALL")
        # Call input dialog for install command
        print(f"DEBUG: libraryfinder.py LibraryFinderPlugin execute_library_install ASK for command to  install:"
              f" message={message}")
        self._execute_namespace_update()

    def find_install_command(self, name):
        try:
            plug = self.global_settings['Plugins'][self.name][name]
        except Exception:
            plug = None
        if plug:
            print(f"DEBUG: libraryfinder.py LibrayFinderPlugin find_install_command FOUND name={name} plug={plug}")
            try:
                print(f"DEBUG: libraryfinder.py LibrayFinderPlugin find_install_command COMMAND plug={plug['command']}")
                return self.parse_command(plug['command'])
            except Exception:
                pass
        return False

    def parse_command(self, command: list) -> list:
        try:
            executable = self.global_settings['executable']
        except Exception:
            executable = sys.executable
        print(f"DEBUG: libraryfinder.py LibrayFinderPlugin parse_command executable={executable}")
        parsed = []
        for cmd in command:
            parsed.append(cmd.replace('%executable', executable))
        return parsed

    def run_install(self, library_name, command):
        # print("DEBUG: Here will be the installation step.") # DEBUG 'pip list'
        from ..run import ui
        result = -1
        for cmd in command:
            config = RunnerCommand(f'Installing {library_name}', cmd, f'Run command: {cmd}')
            # PUBLISHER.subscribe(completed_install, RideRunnerStopped)
            result = ui.Runner(config, self.notebook).run()
        if result == -1:
            print("DEBUG: libraryfinder.py LibrayFinderPlugin run_install FAILED")
            return False
        return True

    def find_documentation_url(self, name):
        try:
            plug = self.global_settings['Plugins'][self.name][name]
        except Exception:
            plug = None
        if plug:
            try:
                print(f"DEBUG: libraryfinder.py LibraryFinderPlugin find_install_command DOC plug={plug['documentation']}")
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

    def _is_valid_path(self, path):
        return path and os.path.isfile(path)

    def _execute_namespace_update(self):
        self.model.update_namespace()

    def _get_path_to_library_spec(self):
        wildcard = (_('Library Spec XML|*.xml|All Files|*.*'))
        dlg = wx.FileDialog(self.frame,
                            message=_('Import Library Spec XML'),
                            wildcard=wildcard,
                            defaultDir=self.model.default_dir)  # DEBUG
        # , style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        else:
            path = None
        dlg.Destroy()
        return path

    def _store_spec(self, path):
        name = get_name_from_xml(path)
        if name:
            shutil.copy(path, os.path.join(context.LIBRARY_XML_DIRECTORY, name+'.xml'))
            message_box = RIDEDialog(title=_('Info'),
                                     message=_('Library "%s" imported\nfrom "%s"\nThis may require RIDE restart.')
                                             % (name, path), style=wx.OK | wx.ICON_INFORMATION)
            message_box.ShowModal()
        else:
            message_box = RIDEDialog(title=_('Import failed'),
                                     message=_('Could not import library from file "%s"')
                                             % path, style=wx.OK | wx.ICON_ERROR)
            message_box.ShowModal()


def completed_install():
    print("DEBUG: libraryfinder.py LibrayFinderPlugin completed_install ENTER")
    wx.CallAfter(wx.App.Get().GetTopWindow().Refresh)
    PUBLISHER.unsubscribe(completed_install, RideRunnerStopped)


@dataclass
class RunnerCommand:
    def __init__(self, name, command, documentation):
        self.name = name
        self.command = command
        self.documentation = documentation
