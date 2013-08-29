#  Copyright 2008-2013 Nokia Siemens Networks Oyj
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
from robotide.action import ActionInfo
from robotide.pluginapi import Plugin

class SpecImporterPlugin(Plugin):

    HEADER = 'Import Library Spec XML'

    def enable(self):
        self.register_action(ActionInfo('Tools', self.HEADER, self.show_spec_import_dialog))

    def show_spec_import_dialog(self, event):
        wildcard = ('Library Spec XML | *.xml')
        dlg = wx.FileDialog(self.frame,
                            message='Import Library Spec XML',
                            wildcard=wildcard,
                            defaultDir=self.model.default_dir,
                            style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        else:
            path = None
        dlg.Destroy()
        print path
        return path