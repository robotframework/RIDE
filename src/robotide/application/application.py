#  Copyright 2008-2009 Nokia Siemens Networks Oyj
#  
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#      http://www.apache.org:licenses/LICENSE-2.0
#  
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import sys
import wx

from robotide.robotapi import ROBOT_VERSION
from robotide.publish import RideOpenSuite, RideOpenResource
from robotide.errors import DataError, NoRideError
from robotide.ui import RideFrame
from robotide import context
from robotide import utils

from datamodel import DataModel
from pluginloader import PluginLoader


class RIDE(wx.App):

    def __init__(self, path=None):
        self._path = path
        context.APP = self
        wx.App.__init__(self, redirect=False)

    def OnInit(self):
        self._check_robot_version()
        self.model = None
        self.frame = RideFrame(self, _KeywordFilter(self))
        self._plugin_loader = PluginLoader(self, self._get_plugin_dirs(),
                                           context.get_core_plugins())
        self.open_suite(self._path)
        self.frame.tree.populate(self.model)
        return True

    def _get_plugin_dirs(self):
        return [context.SETTINGS.get_path('plugins'),
                os.path.join(context.SETTINGS['install root'], 'site-plugins')]

    def get_plugins(self):
        return self._plugin_loader.plugins

    def _check_robot_version(self):
        if ROBOT_VERSION < '2.1':
            context.LOG.error('You are using an old version (%s) of Robot Framework.\n\n'
                              'RIDE does not work correctly with this version. '
                              'Please upgrade to Robot Framework 2.1 or newer from\n'
                              'http://robotframework.org/.' % ROBOT_VERSION)
            sys.exit(1)

    def open_suite(self, path):
        try:
            self.model = DataModel(path)
            RideOpenSuite(path=path).publish()
        except (DataError, NoRideError), err:
            self.model = DataModel()
            context.LOG.error(str(err))

    def open_resource(self, path, datafile=None):
        try:
            resource = self.model.open_resource(path, datafile)
        except DataError, err:
            context.LOG.error(str(err))
            resource = None
        if resource:
            RideOpenResource(path=resource.source).publish()
            self.frame.tree.add_resource(resource)

    def import_new_resource(self, datafile, path):
        self.open_resource(path, datafile)

    def get_all_keywords(self):
        return self.model and self.model.get_all_keywords() or []

    def ok_to_exit(self):
        if self.model.is_dirty():
            ret = wx.MessageBox('There are unsaved modifications.\nDo you want to save your changes before exiting?',
                                'Warning', wx.ICON_WARNING|wx.CANCEL|wx.YES_NO)
            if ret == wx.CANCEL:
                return False
            if ret == wx.YES:
                self.save()
        return True

    def ok_to_open_new(self):
        if self.model.is_dirty():
            ret = wx.MessageBox('There are unsaved modifications.\nDo you want to proceed without saving?',
                                'Warning', wx.ICON_WARNING|wx.YES_NO)
            return ret == wx.YES
        return True

    def get_files_without_format(self, datafile=None):
        return self.model.get_files_without_format(datafile)

    def save(self, datafile=None):
        self.model.serialize(datafile)


class _KeywordFilter(object):

    def __init__(self, app):
        self._app = app
        self.refresh()

    def refresh(self):
        self.keywords = self._app.get_all_keywords()

    def search(self, pattern, search_docs):
        self.keywords = [ kw for kw in self._app.get_all_keywords() if \
                          self._matches_search_criteria(kw, pattern, search_docs) ]
        return self.keywords

    def get_documentation(self, index):
        item = self.keywords[index]
        return utils.html_escape('Arguments: %s\n\n%s' % (item.args, item.doc))

    def _matches_search_criteria(self, kw, pattern, search_docs):
        if utils.contains(kw.name, pattern, ignore=['_']):
            return True
        return search_docs and utils.contains(kw.doc, pattern)
