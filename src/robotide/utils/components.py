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

    def OnLinkClicked(self, link):
        webbrowser.open(link.Href)

    def close(self):
        self.Show(False)

    def clear(self):
        self.SetPage('')


class RidePopupWindow(wx.PopupWindow):

    def __init__(self, parent, size):
        wx.PopupWindow.__init__(self, parent)
        self.SetSize(size)
        self._details = RideHtmlWindow(self, size=size)

    def set_content(self, content):
        color = ''.join([hex(item)[2:] for item in context.POPUP_BACKGROUND])
        details = '<body bgcolor=#%s>%s</body>' % (color, content)
        self._details.SetPage(details)


class MacRidePopupWindow(wx.Window):
    """Mac version of RidePopupWindow with very limited functionality.

    wx.PopupWindow does not work on Mac and without this hack RIDE could
    not be used on that platform at all.
    """

    def __init__(self, parent, size):
        wx.Window.__init__(self, parent)

    def set_content(self, content):
        pass

    def IsShown(self):
        return False


if wx.PlatformInfo[0] == '__WXMAC__':
    RidePopupWindow = MacRidePopupWindow
del MacRidePopupWindow


class PopupMenu(wx.Menu):

    def __init__(self, parent, menu_items):
        wx.Menu.__init__(self)
        for item in menu_items:
            name, shortcut = self._get_name(item)
            if name == '---':
                self.AppendSeparator()
            else:
                self._add_item(parent, name, shortcut)
        parent.PopupMenu(self)
        self.Destroy()

    def _get_name(self, item):
        if isinstance(item, basestring):
            return item, None
        return item

    def _add_item(self, parent, name, shortcut):
        handler = getattr(parent, 'On'+name.replace(' ', ''))
        if shortcut:
            name = '%s\t%s' % (name, shortcut)
        id_ = wx.NewId()
        self.Append(id_, name)
        parent.Bind(wx.EVT_MENU, handler, id=id_)
