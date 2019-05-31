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
from robotide.lib.robot.utils.compat import with_metaclass

class eventhandlertype(type):
    def __new__(cls, name, bases, dict):
        def mod_time_wrapper(method):
            def wrapped(self, event=None):
                # First condition is guard against dead object
                if self and self._can_be_edited(event):
                    method(self, event)
            return wrapped
        for attr in dict:
            if (attr.startswith('On') and
                    not (name == 'RideFrame' and attr == 'OnClose') and
                    not (name == 'Tree' and attr == 'OnDrop') and
                    not (name == 'KeywordEditor' and attr == 'OnIdle') and
                    not (attr == 'OnEnterWindow' or attr == 'OnLeaveWindow' or attr == 'OnDisplayMotion')):
                dict[attr] = mod_time_wrapper(dict[attr])
        return type.__new__(cls, name, bases, dict)


class RideEventHandler(with_metaclass(eventhandlertype, object)):
    _SHOWING_MODIFIED_ON_DISK_CONTROLLERS_ = set()
    _SHOWING_REMOVED_ON_DISK_CONTROLLERS_ = set()

    def _can_be_edited(self, event):
        ctrl = self.get_selected_datafile_controller()
        if ctrl and ctrl.has_been_removed_from_disk():
            return self._show_removed_from_disk_warning(ctrl, event)
        if ctrl and ctrl.has_been_modified_on_disk():
            return self._show_modified_on_disk_warning(ctrl, event)
        return True

    def _show_removed_from_disk_warning(self, ctrl, event):
        msg = ['The file has been removed from the file system.',
               'Do you want to remove it from the project?',
               'Answering <No> will rewrite the file on disk.']
        self._execute_if_not_in_the_set(RideEventHandler._SHOWING_REMOVED_ON_DISK_CONTROLLERS_, ctrl, msg, ctrl.remove)

    #TODO: Not a very good mechanism to control the number of shown dialogs
    def _show_modified_on_disk_warning(self, ctrl, event):
        def reload_datafile():
            ctrl.reload()
            self.refresh_datafile(ctrl, event)
        msg = ['The file has been changed on the file system.',
               'Do you want to reload the file?',
               'Answering <No> will overwrite the changes on disk.']
        self._execute_if_not_in_the_set(RideEventHandler._SHOWING_MODIFIED_ON_DISK_CONTROLLERS_, ctrl, msg, reload_datafile)

    def _execute_if_not_in_the_set(self, the_set, ctrl, msg, yes_handler):
        if ctrl in the_set:
            return
        the_set.add(ctrl)
        wx.CallLater(100, self._try_show_warning, the_set, ctrl, msg, yes_handler)

    def _try_show_warning(self, the_set, ctrl, msg, yes_handler):
        try:
            self._show_warning(msg, ctrl, yes_handler)
        finally:
            the_set.remove(ctrl)

    def _show_warning(self, msg_lines, ctrl, yes_handler):
        if ctrl.dirty:
            msg_lines.insert(2, 'Answering <Yes> will discard unsaved changes.')
        msg_lines.extend(['', 'Changed file is:', ctrl.datafile.source])
        ret = wx.MessageBox('\n'.join(msg_lines), 'File Changed On Disk',
                            style=wx.YES_NO|wx.ICON_WARNING)
        if ret == wx.NO:
            from robotide.controller.ctrlcommands import SaveFile
            ctrl.execute(SaveFile())
            return True
        if ret == wx.YES:
            yes_handler()
        return False

    def get_selected_datafile_controller(self):
        raise NotImplementedError(self.__class__.__name__)
