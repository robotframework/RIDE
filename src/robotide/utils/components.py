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

import webbrowser
import wx
from wx.html import HtmlWindow

from robotide import context


class RideHtmlWindow(HtmlWindow):

    def __init__(self, parent, size=wx.DefaultSize, text=None):
        HtmlWindow.__init__(self, parent, style=wx.BORDER_SUNKEN, size=size)
        self.SetBorders(2)
        self.SetStandardFonts()
        if text:
            self.SetPage(text)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)

    def OnKey(self, event):
        self.Parent.OnKey(event)
        event.Skip()

    def OnLinkClicked(self, link):
        webbrowser.open(link.Href)

    def close(self):
        self.Show(False)

    def clear(self):
        self.SetPage('')


class PopupMenu(wx.Menu):

    def __init__(self, parent, menu_items):
        wx.Menu.__init__(self)
        for item in menu_items:
            if item.is_separator():
                self.AppendSeparator()
            else:
                self._add_item(parent, item)
        parent.PopupMenu(self)
        self.Destroy()

    def _add_item(self, parent, item):
        id_ = wx.NewId()
        self.Append(id_, item.name)
        parent.Bind(wx.EVT_MENU, item.callable, id=id_)


class PopupMenuItems(object):

    def __init__(self, parent=None, menu_names=[]):
        self._items = []
        for item in menu_names:
            self.add_menu_item(PopupMenuItem(item, parent=parent))

    def __iter__(self):
        return iter(self._items)

    def add_menu_item(self, item):
        self._items.append(item)

    def add_separator(self):
        self.add_menu_item(PopupMenuItem('---'))


class PopupMenuItem(object):

    def __init__(self, name, callable=None, parent=None):
        self.name = name
        self.callable = self._get_callable(name, callable, parent)

    def _get_callable(self, name, callable, parent):
        if callable:
            return callable
        if name == '---':
            return None
        handler_name = name.replace(' ', '').split('\t')[0]  # split shortcut
        return getattr(parent, 'On'+handler_name)

    def is_separator(self):
        return self.name == '---'


class ButtonWithHandler(wx.Button):

    def __init__(self, parent, label, handler=None, width=-1,
                 height=context.SETTING_ROW_HEIGTH, style=wx.NO_BORDER):
        wx.Button.__init__(self, parent, style=style, label=label,
                           size=(width, height))
        if not handler:
            handler = getattr(parent, 'On'+label.replace(' ', ''))
        parent.Bind(wx.EVT_BUTTON, handler, self)
