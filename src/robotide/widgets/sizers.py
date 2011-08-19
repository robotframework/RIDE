#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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
        wx.BoxSizer.__init__(self, self.direction)

    def add(self, component):
        self.Add(component)

    def add_with_padding(self, component, padding):
        self.Add(component, flag=wx.ALL, border=padding)

    def add_expanding(self, component):
        self.Add(component, 1, wx.EXPAND)


class VerticalSizer(_BoxSizer):
    direction = wx.VERTICAL


class HorizontalSizer(_BoxSizer):
    direction = wx.HORIZONTAL

    def add_to_end(self, component):
        self.Add(component, flag=wx.ALIGN_RIGHT)

