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


class Font(object):
    help = property(lambda self: self._get_font(scale=-2))
    fixed = property(lambda self: self._get_font(family=wx.FONTFAMILY_MODERN))
    fixed_log = property(lambda self:
            self._get_font(scale=-2, family=wx.FONTFAMILY_MODERN))
    underlined = property(lambda self: self._get_font(underlined=True))

    def _get_font(self, scale=0, family=wx.FONTFAMILY_DEFAULT, underlined=False):
        size = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT).GetPointSize() + scale
        return wx.Font( size, family, wx.FONTSTYLE_NORMAL,
                        wx.FONTWEIGHT_NORMAL, underline=underlined)
