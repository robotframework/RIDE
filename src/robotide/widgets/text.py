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
from wx import Size


class TextField(wx.SearchCtrl):

    def __init__(self, parent, initial_value, process_enters=False, size=Size(200, 32)):
        flags = wx.TE_PROCESS_ENTER|wx.TE_LEFT if process_enters else wx.TE_LEFT
        wx.SearchCtrl.__init__(self, parent, size=size, style=flags|wx.TE_NOHIDESEL)
        self.SetValue(initial_value)
