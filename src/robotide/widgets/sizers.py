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
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            wx.BoxSizer.__init__(self, self.orient)
        else:
            wx.BoxSizer.__init__(self, self.direction)



    def add(self, component, proportion=0, flag=0):
        self.Add(component, proportion=proportion, flag=flag)

    def add_with_padding(self, component, padding=5):
        self.Add(component, flag=wx.ALL, border=padding)

    def add_expanding(self, component, propotion=1, padding=0):
        self.Add(component, proportion=propotion, flag=wx.EXPAND | wx.ALL,
                 border=padding)


class VerticalSizer(_BoxSizer):
    orient = direction = wx.VERTICAL


class HorizontalSizer(_BoxSizer):
    orient = direction = wx.HORIZONTAL

    def add_to_end(self, component):
        self.Add(component, flag=wx.ALIGN_RIGHT)
