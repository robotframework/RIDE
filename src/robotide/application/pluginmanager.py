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

import os
import imp
import inspect

from robotide.context import SETTINGS, LOG
from robotide import utils

from plugin import Plugin


class PluginManager(object):

    def __init__(self, application):
        self.plugins = [ PluginFactory(application, cls)
                         for cls in self._find_plugin_classes() ]

    def _find_plugin_classes(self):
        for cls in self._get_standard_plugin_classes():
            yield cls
        for path in self._find_plugin_files():
            for cls in self._import_classes(path):
                if issubclass(cls, Plugin) and cls is not Plugin:
                    yield cls

    def _get_standard_plugin_classes(self):
        from releasenotes import ReleaseNotesPlugin
        from plugingui import PluginManagerPlugin
        from recentfiles import RecentFilesPlugin 
        from preview import PreviewPlugin
        from gridcolorizer import Colorizer
        return [ReleaseNotesPlugin, PluginManagerPlugin, RecentFilesPlugin,
                PreviewPlugin, Colorizer]

    def _find_plugin_files(self):
        plugindirs = [SETTINGS.get_path('plugins'),
                      os.path.join(SETTINGS['install root'], 'site-plugins')]
        for path in plugindirs:
            if os.path.exists(path):
                for filename in os.listdir(path):
                    if os.path.splitext(filename)[1].lower() == ".py":
                        yield os.path.join(path, filename)

    def _import_classes(self, path):
        dirpath, filename = os.path.split(path)
        modulename = os.path.splitext(filename)[0]
        file, imppath, description = imp.find_module(modulename, [dirpath])
        try:
            module = imp.load_module(modulename, file, imppath, description)
        except Exception, err:
            LOG.error("Importing plugin module '%s' failed:\n%s" % (path, err))
            return []
        finally:
            if file:
                file.close()
        return [ cls for _, cls in 
                 inspect.getmembers(module, predicate=inspect.isclass) ]


def PluginFactory(application, plugin_class):
    try:
        plugin = plugin_class(application)
    except Exception, err:
        return BrokenPlugin(str(err), plugin_class)
    else:
        return PluginWrapper(application, plugin)


class _PluginWrapper(object):

    def __init__(self, name, doc='', error=None):
        self.name = name
        self.doc = doc
        self.error = error
        self.active = False
        self.config_panel = lambda self: None


class PluginWrapper(_PluginWrapper):

    def __init__(self, application, plugin):
        _PluginWrapper.__init__(self, plugin.name, plugin.doc)
        self.config_panel = plugin.config_panel
        self.activate = plugin.activate
        self.deactivate = plugin.deactivate
        if SETTINGS['plugins'].get(plugin.name, plugin.initially_active):
            plugin.activate()
            self.active = True


class BrokenPlugin(_PluginWrapper):

    def __init__(self, error, plugin_class):
        name = utils.name_from_class(plugin_class, 'Plugin')
        _PluginWrapper.__init__(self, name, error=error)
        LOG.error("Taking %s plugin into use failed:\n%s" % (name, error))
