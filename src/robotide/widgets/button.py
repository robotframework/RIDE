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


class ButtonWithHandler(wx.Button):

    def __init__(self, parent, label, handler=None, width=-1,
                 height=25):
        wx.Button.__init__(self, parent, label=label,
                           size=(width, height))
        if not handler:
            handler = getattr(parent, 'On'+label.replace(' ', ''))
        parent.Bind(wx.EVT_BUTTON, handler, self)
