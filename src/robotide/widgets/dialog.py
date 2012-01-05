#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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

class Dialog(wx.Dialog):

    def __init__(self, title='', parent=None, size=None, style=None):
        parent = parent or wx.GetTopLevelWindows()[0]
        size = size or (-1, -1)
        # wx.THICK_FRAME allows resizing
        style = style or wx.DEFAULT_DIALOG_STYLE | wx.THICK_FRAME
        wx.Dialog.__init__(self, parent, title=title, size=size, style=style)
        self.CenterOnParent()

    def _create_buttons(self, sizer):
        buttons = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
        sizer.Add(buttons, flag=wx.ALIGN_CENTER|wx.ALL, border=5)

    def _create_horizontal_line(self, sizer):
        line = wx.StaticLine(self, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, flag=wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP,
                  border=5)

    def execute(self):
        retval = None
        if self.ShowModal() == wx.ID_OK:
            retval = self._execute()
        self.Destroy()
        return retval

    def _execute(self):
        raise NotImplementedError(self.__class__.__name__)
