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

import builtins
import os
import shutil
import wx

from .. import context
from ..action import ActionInfo
from ..pluginapi import Plugin
from ..publish import PUBLISHER, RideExecuteSpecXmlImport
from .xmlreaders import get_name_from_xml

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class SpecImporterPlugin(Plugin):

    HEADER = _('Import Library Spec XML')

    def enable(self):
        self.register_action(ActionInfo(_('Tools'), self.HEADER,
                                        self.execute_spec_import, position=83))
        PUBLISHER.subscribe(self._ps_on_execute_spec_import, RideExecuteSpecXmlImport)

    def disable(self):
        self.unsubscribe_all()
        self.unregister_actions()

    def _ps_on_execute_spec_import(self, message):
        self.execute_spec_import()

    def execute_spec_import(self):
        path = self._get_path_to_library_spec()
        if self._is_valid_path(path):
            self._store_spec(path)
            self._execute_namespace_update()

    def _is_valid_path(self, path):
        return path and os.path.isfile(path)

    def _execute_namespace_update(self):
        self.model.update_namespace()

    def _get_path_to_library_spec(self):
        wildcard = (_('Library Spec XML|*.xml|All Files|*.*'))
        dlg = wx.FileDialog(self.frame,
                            message=_('Import Library Spec XML'),
                            wildcard=wildcard,
                            defaultDir=self.model.default_dir)  # DEBUG
        # , style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        else:
            path = None
        dlg.Destroy()
        return path

    def _store_spec(self, path):
        name = get_name_from_xml(path)
        if name:
            shutil.copy(path, os.path.join(context.LIBRARY_XML_DIRECTORY, name+'.xml'))
            wx.MessageBox(_('Library "%s" imported\nfrom "%s"\nThis may require RIDE restart.') % (name, path),
                          _('Info'), wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox(_('Could not import library from file "%s"') % path, _('Import failed'),
                          wx.OK | wx.ICON_ERROR)
