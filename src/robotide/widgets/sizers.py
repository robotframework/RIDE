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


class _BoxSizer(wx.BoxSizer):

    def __init__(self):
        wx.BoxSizer.__init__(self, orient=self.orientation)
        # print(f"DEBUG: _BoxSizer __init__ after super init, orientation is {self.orientation}")

    def add_sizer(self, component, proportion=0, flag=0):
        # self.Add(component, proportion=proportion, flag=flag)
        self.Add(component, wx.SizerFlags(proportion).Align(flag))

    def add_with_padding(self, component, padding=5):
        # self.Add(component, flag=wx.ALL, border=padding)
        self.Add(component, wx.SizerFlags(0).Border(wx.ALL, padding))

    def add_expanding(self, component, propotion=1, padding=0):
        # self.Add(component, proportion=propotion, flag=wx.EXPAND | wx.ALL,
        #         border=)
        self.Add(component, wx.SizerFlags(propotion).Expand().Border(wx.ALL, padding))


class VerticalSizer(_BoxSizer):

    def __init__(self):
        self.orientation = wx.VERTICAL
        _BoxSizer.__init__(self)


class HorizontalSizer(_BoxSizer):

    def __init__(self):
        self.orientation = wx.HORIZONTAL
        _BoxSizer.__init__(self)

    def add_to_end(self, component):
        # self.Add(component, flag=wx.ALIGN_RIGHT)
        self.Add(component, wx.SizerFlags().Align(wx.ALIGN_RIGHT))
