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
import pickle


class GridClipboard(object):
    """Implements a "smart" clipboard. String objects are saved as usual, but
    other python objects can be saved as well. The primary purpose is to place
    a list of grid rows on the clipboard.
    """

    def is_empty(self):
        # For some reason, empty contents in the clipboard on Windows is '\x00\x00'
        # WTF?!?!?!?
        cont = self.get_contents()
        if isinstance(cont, basestring):
            cont = cont.replace('\x00', '')
        return not cont 
    
    def set_contents(self, data):
        do = PythonDataObject()
        do.SetData(pickle.dumps(data))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(do)
        wx.TheClipboard.Close()

    def get_contents(self):
        """Gets contents of the clipboard, returning a python object if
        possible, otherwise returns plain text or None if the clipboard is
        empty.
        """
        wx.TheClipboard.Open()
        try:
            return self._get_value()
        finally:
            wx.TheClipboard.Close()

    def _get_value(self):
        try:
            do = PythonDataObject()
            wx.TheClipboard.GetData(do)
            return pickle.loads(do.GetDataHere())
        except TypeError:
            try:
                do = wx.TextDataObject()
                wx.TheClipboard.GetData(do)
                # For some reason, when getting string contents from the 
                # clipboard on Windows '\x00' is inserted between each char.
                # WTF?!?!?!?
                data =  do.GetDataHere()
                if data:
                    return data.replace('\x00', '')
            except TypeError:
                pass
        return None


class PythonDataObject(wx.PyDataObjectSimple):

    def __init__(self):
        wx.PyDataObjectSimple.__init__(self, wx.CustomDataFormat('PythonDataObject'))
        self.data = None

    def GetDataSize(self):
        return len(self.data)

    def GetDataHere(self):
        return self.data

    def SetData(self, data):
        self.data = data
        return True


GRID_CLIPBOARD = GridClipboard()

