#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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


import os.path
import re
import wx

from plugin import Plugin


class RecentFilesPlugin(Plugin):
    """Add recently opened files to the file menu.

    This is still very experimental, use at your own risk.
    """
    PERSISTENT_ATTRIBUTES = {'recent_files':[], 'max_number_of_files':4}

    def __init__(self, application=None):
        Plugin.__init__(self, application)
        self.version = "0.1"
        self._menuitems = []
        self._file = {}

    def activate(self):
        """Make the plugin available for use."""
        # If there is a currently open file, add it to the top of the list
        self._remember_current_file()
        self._update_file_menu()
        self.subscribe(self.OnPublication, ("core", "open","suite"))
        # This plugin doesn't currently support resources
#        self._frame.subscribe(self.OnPublication, ("core", "open","resource"))

    def deactivate(self):
        """Deactivates this plugin."""
        self._remove_from_file_menu()
        self.unsubscribe(self.OnPublication)

    def OnAbout(self, event):
        """Displays a dialog about this plugin."""
        info = wx.AboutDialogInfo()
        info.Name = self.name
        info.Version = self.version
        info.Description = self.__doc__
        info.Developers = ["Bryan Oakley, Orbitz Worldwide"]
        wx.AboutBox(info)

    def OnOpenRecent(self, event):
        """Event handler used to open a recent file."""
        id = event.GetId()
        if not self.new_suite_can_be_opened():
            return
        path = self._normalize(self._file[id])
        # There needs to be a better way. This assumes the path is a
        # suite but it could be a resource. There needs to be a
        # generic "open" command in the application or frame object
        # that Does The Right Thing no matter what the type.
        self.open_suite(path)

    def OnPublication(self,message):
        """Saves the path of a file when it is opened."""
        self._remember_file(message.data["path"])

    def _add_menuitem(self, menu, file, n=0):
        """Add a menuitem to the given menu. 

        file may be one of the following:
        '---' adds a separator, 
        '' adds a disabled "no files available" item
        anything else represents a filename as a string

        """

        id = wx.NewId()
        pos = menu.GetMenuItemCount()-1
        if file == "---":
            menuitem = menu.InsertSeparator(pos)
        elif file == "":
            menuitem = menu.Insert(pos,id, "no recent files")
            menuitem.Enable(False)
        else:
            file = self._normalize(file)
            filename = os.path.basename(file)
            menuitem = menu.Insert(pos,id, "&%s: %s" % (n+1, filename), "Open %s" % file)
            wx.EVT_MENU(self.get_frame(), id, self.OnOpenRecent)
            self._file[id] = file
        self._menuitems.append(menuitem)

    def _get_file_menu(self):
        """Return a handle to the File menu on the menubar."""
        menubar = self.get_menu_bar()
        pos = menubar.FindMenu("File")
        file_menu = menubar.GetMenu(pos)
        return file_menu

    def _normalize(self, path):
        """If path matches */__init__.*, return the directory otherwise return the original path.""" 
        path = os.path.abspath(path)
        if re.match("__init__.*", os.path.basename(path)):
            # represents a directory suite, use the actual directory name instead
            path = os.path.dirname(path)
        return path

    def _remember_current_file(self):
        """Save the currently loaded suite, if there is one"""
        model = self.get_model()
        if model and model.suite:
            self._remember_file(model.suite.source)

    def _remember_file(self, file):
        """Add a filename to the list of recent files."""
        if not file:
            return
        file = self._normalize(file)
        if file not in self.recent_files:
            self.recent_files.insert(0,file)
            self.recent_files = self.recent_files[0:self.max_number_of_files]
            self._update_file_menu()

    def _remove_from_file_menu(self):
        """Remove the menubar item from the menubar for this plugin."""
        file_menu = self._get_file_menu()
        for menuitem in self._menuitems:
            file_menu.DeleteItem(menuitem)
        self._menuitems = []
        self._file = {}

    def _update_file_menu(self):
        """Add all of the known recent files to the file menu."""
        self._remove_from_file_menu()
        file_menu = self._get_file_menu()
        if len(self.recent_files) == 0:
            self._add_menuitem(file_menu, "")
        else:
            for n, file in enumerate(self.recent_files):
                self._add_menuitem(file_menu, file, n)
        self._add_menuitem(file_menu, "---")

