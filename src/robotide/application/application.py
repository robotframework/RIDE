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
import time
from threading import Thread

from robotide.robotapi import ROBOT_VERSION
from robotide.namespace import Namespace
from robotide.publish import RideOpenSuite, RideOpenResource
from robotide.errors import DataError, NoRideError
from robotide.ui import RideFrame
from robotide import context

from datamodel import DataModel
from pluginloader import PluginLoader


class RIDE(wx.App):

    def __init__(self, path=None):
        self._initial_path = path
        context.APP = self
        wx.App.__init__(self, redirect=False)

    def OnInit(self):
        self._check_robot_version()
        self.model = None
        self.frame = RideFrame(self)
        self.namespace = Namespace()
        self._editor_classes = {}
        self._plugin_loader = PluginLoader(self, self._get_plugin_dirs(),
                                           context.get_core_plugins())
        self._plugin_loader.enable_plugins()
        self.open_suite(self._initial_path)
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
        self.model = self._load_suite(path)
        RideOpenSuite(path=path).publish()
        context.LOG.report_parsing_errors()

    def _load_suite(self, path):
        progress_dialog = wx.ProgressDialog('RIDE', 'Loading the test data',
                                            maximum=100, parent=self.frame,
                                            style = wx.PD_ELAPSED_TIME)
        loader = _DataLoader(self.namespace, path)
        loader.start()
        while loader.isAlive():
            time.sleep(0.1)
            progress_dialog.Pulse()
        progress_dialog.Destroy()
        return loader.model

    def open_resource(self, path, datafile=None):
        try:
            resource = self.model.open_resource(path, datafile)
        except DataError, err:
            context.LOG.error(str(err))
            resource = None
        if resource:
            RideOpenResource(path=resource.source).publish()
            self.frame.add_resource(resource)

    def import_new_resource(self, datafile, path):
        self.open_resource(path, datafile)

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

    def register_editor(self, object_class, editor_class):
        '''Register 'editor_class' as an editor class for objects of type 'object_class'''
        if object_class not in self._editor_classes:
            self._editor_classes[object_class] = [editor_class]
        else:
            # insert it at the head of the list; the tail of the list
            # is considered to be the current editor
            if editor_class not in self._editor_classes[object_class]:
                self._editor_classes[object_class].insert(0, editor_class)

    def unregister_editor(self, object_class, editor_class):
        '''Unregisters 'editor_class' as an editor class for objects of type 'object_class'''
        if object_class not in self._editor_classes:
            return
        else:
            if editor_class in self._editor_classes[object_class]:
                self._editor_classes[object_class].remove(editor_class)

    def set_editor(self, object_class, editor_class):
        '''Designate which editor class to use for the given object class

        The notion of "current editor" is merely whichever one is at the
        end of the list.
        '''
        if object_class not in self._editor_classes:
            self._editor_classes[object_class] = [editor_class]
        else:
            if editor_class in self._editor_classes[object_class]:
                self._editor_classes[object_class].remove(editor_class)
            self._editor_classes[object_class].append(editor_class)

    def get_editors(self, object_class):
        '''Return all registered editors for the given object class'''
        return self._editor_classes.get(object_class, [])
        
    def get_editor(self, object_class):
        '''Return the current editor class for the given object class'''
        class_list = self._editor_classes.get(object_class, [])
        if len(class_list) > 0:
            editor_class = class_list[-1]
        else:
            editor_class = None
        return editor_class


class _DataLoader(Thread):

    def __init__(self, namespace, path):
        Thread.__init__(self)
        self._path = path
        self._namespace = namespace
        self.model = None

    def run(self):
        try:
            self.model = DataModel(self._namespace, self._path)
        except (DataError, NoRideError), err:
            context.LOG.error(str(err))
            self.model = DataModel(self._namespace)

