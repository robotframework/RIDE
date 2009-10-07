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

import wx

from robotide import context


def create_button(parent, label, evt_handler=None, width=-1,
                  height=context.SETTING_ROW_HEIGTH, style=wx.NO_BORDER):
    btn = wx.Button(parent, style=style, label=label, size=(width, height))
    if evt_handler:
        parent.Bind(wx.EVT_BUTTON, evt_handler, btn)
    return btn


def create_toolbar(parent, style, toolbardata, size=(16,16)):
    tb = wx.ToolBar(parent, -1, style=style)
    tb.SetToolBitmapSize(size)
    for imgpath, name, help, handler in toolbardata: 
        _create_tool(parent, tb, imgpath, name, help, handler)
    tb.Realize()
    return tb
    
def _create_tool(parent, tb, img_or_path, name, help, handler):
    id = wx.NewId()
    if isinstance(img_or_path, basestring):
        bmp = wx.Image(img_or_path, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
    else:
        bmp = img_or_path
    tool = tb.AddLabelTool(id, name, bmp, shortHelp=name, longHelp=help)
    parent.Bind(wx.EVT_TOOL, handler, tool)
