#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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

from .font import Font


class Label(wx.StaticText):

    def __init__(self, parent, id=-1, label='', **args):
        wx.StaticText.__init__(self, parent=parent, id=id, label=label.replace('&', '&&'), **args)

    def SetLabel(self, label):
        wx.StaticText.SetLabel(self, label.replace('&', '&&'))


class HeaderLabel(Label):

    def __init__(self, parent, label):
        Label.__init__(self, parent, label=label)
        self.SetFont(wx.Font(wx.FontInfo(12).Family(wx.FONTFAMILY_SWISS).Bold()))


class HelpLabel(Label):

    def __init__(self, parent, label):
        Label.__init__(self, parent, label=label)
        self.SetFont(Font().help)
