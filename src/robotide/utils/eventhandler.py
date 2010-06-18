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


class eventhandlertype(type):
    def __new__(cls, name, bases, dict):
        def mod_time_wrapper(method):
            def wrapped(self, event=None):
                if self._can_be_edited(event):
                    method(self, event)
            return wrapped
        for attr in dict:
            if attr.startswith('On') and \
                    not (name == 'RideFrame' and attr == 'OnClose') and \
                    not (name == 'Tree' and attr == 'OnDrop') and \
                    not (name == 'KeywordEditor' and attr == 'OnIdle'):
                dict[attr] = mod_time_wrapper(dict[attr])
        return type.__new__(cls, name, bases, dict)


class RideEventHandler(object):
    __metaclass__ = eventhandlertype

    def _can_be_edited(self, event):
        ctrl = self.get_selected_datafile_controller()
        if ctrl and ctrl.has_been_modified_on_disk():
            return self._show_modified_on_disk_warning(ctrl, event)
        return True

    def _show_modified_on_disk_warning(self, ctrl, event):
        msg = ['The file has been changed on the file system.',
               'Do you want to reload the file?',
               'Answering <No> will overwrite the changes on disk.']
        if ctrl.dirty:
            msg.insert(2, 'Answering <Yes> will discard unsaved changes.')
        ret = wx.MessageBox('\n'.join(msg), 'File Modified',
                            style=wx.YES_NO|wx.CANCEL|wx.ICON_WARNING)
        if ret == wx.YES:
            ctrl.reload()
            self.refresh_datafile(ctrl, event)
            return True
        elif ret == wx.NO:
            ctrl.save()
            return True
        else:
            return False

    def get_selected_datafile_controller(self):
        raise NotImplementedError(self.__class__.__name__)
