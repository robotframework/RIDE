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

from robotide.context import LOG
from robotide import utils


def PluginFactory(application, plugin_class):
    try:
        plugin = plugin_class(application)
    except Exception, err:
        return BrokenPlugin(str(err), plugin_class)
    else:
        return PluginConnector(application, plugin)


class _PluginConnector(object):

    def __init__(self, name, doc='', error=None):
        self.name = name
        self.doc = doc
        self.error = error
        self.active = False
        self.metadata = {}
        self.config_panel = lambda self: None


class PluginConnector(_PluginConnector):

    def __init__(self, application, plugin):
        _PluginConnector.__init__(self, plugin.name, plugin.doc)
        self._plugin = plugin
        self.config_panel = plugin.config_panel
        self.metadata = plugin.metadata 
        if plugin._settings.get('active', plugin.initially_active):
            self.activate()

    def activate(self):
        self._plugin.activate()
        self.active = True
        self._plugin._settings.set('active', True)

    def deactivate(self):
        self._plugin.deactivate()
        self.active = False
        self._plugin._settings.set('active', False)


class BrokenPlugin(_PluginConnector):

    def __init__(self, error, plugin_class):
        name = utils.name_from_class(plugin_class, 'Plugin')
        doc = 'This plugin is disabled because it failed to load properly.\n' \
               + 'Error: ' + error
        _PluginConnector.__init__(self, name, doc=doc, error=error)
        LOG.error("Taking %s plugin into use failed:\n%s" % (name, error))

