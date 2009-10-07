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


import wx


class _ActionItem(object):

    def __init__(self, name, doc):
        self.name = name
        self.doc = doc
        self.id = wx.NewId()
        self.handler_name = 'On%s' % self.name.replace(' ', '')

    def bind(self, parent, component):
        parent.Bind(self.event, getattr(parent, self.handler_name), component)


class MenuActionItem(_ActionItem):
    event = wx.EVT_MENU

    def __init__(self, name, doc='', accelerator='', shortcut=''):
        _ActionItem.__init__(self, name, doc)
        self.menu_entry = self._get_menu_entry(name, accelerator, shortcut)
        self.is_separator = self.menu_entry == '---'

    def _get_menu_entry(self, name, accelerator, shortcut):
        menu_name = self._get_menu_name(name, accelerator)
        if shortcut:
            menu_name = '%s\t%s' % (menu_name, shortcut)
        return menu_name

    def _get_menu_name(self, name, accelerator):
        if not accelerator:
            return name
        start, end = name.split(accelerator, 1)
        return '%s&%s%s' % (start, accelerator, end)


class ToolActionItem(_ActionItem):
    event = wx.EVT_TOOL

    def __init__(self, name, doc, art):
        _ActionItem.__init__(self, name, doc)
        self.art = art


class Actions(object):

    def __init__(self, parent):
        self.parent = parent

    def get_menubar(self):
        return _MenuBar(self.parent)

    def get_toolbar(self):
        return _ToolBar(self.parent)


class _MenuBar(wx.MenuBar):

    def __init__(self, parent):
        wx.MenuBar.__init__(self)
        self.Append(_Menu(parent, _FileMenuData), '&File')
        self.Append(_Menu(parent, _EditMenuData), '&Edit')
        self.Append(_Menu(parent, _ToolsMenuData), '&Tools')
        self.Append(_Menu(parent, _NavigateMenuData), '&Navigate')
        self.Append(_Menu(parent, _HelpMenuData), '&Help')


class _Menu(wx.Menu):

    def __init__(self, parent, items):
        wx.Menu.__init__(self)
        for item in items:
            if item.is_separator:
                self.AppendSeparator()
            else:
                self._create_menu_item(parent, item)

    def _create_menu_item(self, parent, item):
        menuitem = self.Append(item.id, item.menu_entry, item.doc)
        item.bind(parent, menuitem)


class _ToolBar(wx.ToolBar):

    def __init__(self, parent):
        wx.ToolBar.__init__(self, parent, style=wx.TB_HORIZONTAL)
        self.SetToolBitmapSize((16,16))
        for item in _ToolData:
            self.create_tool(item, parent)
        self.Realize()

    def create_tool(self, item, parent):
        bmp = wx.ArtProvider.GetBitmap(item.art, wx.ART_TOOLBAR, (16, 16))
        tool = self.AddLabelTool(item.id, item.name, bmp,
                                 shortHelp=item.name, longHelp=item.doc)
        item.bind(parent, tool)


_OpenItemData = ('Open', 'Open file containing tests')
_OpenDirItemData = ('Open Directory', 'Open dir containing Robot files')
_SaveItemData = ('Save', 'Save current suite or resource')

_FileMenuData = [ MenuActionItem(*args) for args in
                  [_OpenItemData + ('O', 'Ctrl-O'),
                   _OpenDirItemData + ('D', 'Ctrl-Shift-O'),
                   ('Open Resource', 'Open a resource file', 'R', 'Ctrl-R'),
                   ('---', ),
                   ('New Suite', 'Create a new top level suite', 'N', 'Ctrl-N'),
                   ('New Resource', 'Create New Resource File', 'e', 'Ctrl-Shift-N'),
                   ('---', ),
                   _SaveItemData + ('S', 'Ctrl-S'),
                   ('Save All', 'Save all changes', '', 'Ctrl-Shift-S'),
                   ('Save As', 'Save current project with new name'),
                   ('---', ),
                   ('Exit', 'Exit RIDE', 'x', 'Ctrl-Q')]]

_EditMenuData = [ MenuActionItem(*args) for args in
                  [('Undo', 'Undo last modification', 'U', 'Ctrl-Z'),
                  ('---', ),
                  ('Cut', 'Cut from selected cells', 't', 'Ctrl-X'),
                  ('Copy', 'Copy from selected cells', 'C', 'Ctrl-C'),
                  ('Paste', 'Paste to selected cell', 'P', 'Ctrl-V'),
                  ('Delete', 'Delete from selected cells', 'D', 'Del'),
                  ('---', ),
                  ('Comment', 'Comment selected rows', '', 'Ctrl-3'),
                  ('Uncomment', 'Uncomment selected rows', '', 'Ctrl-4')] ]

_ToolsMenuData = [ MenuActionItem(*args) for args in
                   [('Keyword Completion', 'Show available keywords',
                     '', 'Ctrl-Space'),
                    ('Search Keywords',
                     'Search keywords from libraries and resources')] ]

_NavigateMenuData = [ MenuActionItem(*args) for args in
                      [('Go Back', 'Go back to previous location in tree',
                        'B', 'Alt-Left'),
                       ('Go Forward', 'Go forward to next location in tree',
                        'F', 'Alt-Right')] ]

_HelpMenuData = [ MenuActionItem('About', 'Information about RIDE', 'A') ]

_ToolData = [ ToolActionItem(*args) for args in
                  [_OpenItemData + (wx.ART_FILE_OPEN, ),
                   _OpenDirItemData + (wx.ART_FOLDER_OPEN, ),
                   _SaveItemData + (wx.ART_FILE_SAVE, )] ]
