#  Copyright 2008-2015 Nokia Solutions and Networks
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
        return PluginConnector(plugin, application)


class _PluginConnector(object):

    def __init__(self, name, doc='', error=None):
        self.name = name
        self.doc = doc
        self.error = error
        self.enabled = False
        self.metadata = {}
        self.config_panel = lambda self: None


class PluginConnector(_PluginConnector):

    def __init__(self, plugin, application):
        _PluginConnector.__init__(self, plugin.name, plugin.doc)
        self._plugin = plugin
        self._settings = application.settings['Plugins'].add_section(plugin.name)
        self.config_panel = plugin.config_panel
        self.metadata = plugin.metadata

    def enable_on_startup(self):
        if self._settings.get('_enabled', self._plugin.initially_enabled):
            self.enable()

    def enable(self):
        self._settings.set('_enabled', True)
        self.enabled = True
        self._plugin.enable()

    def disable(self):
        if self.enabled:
            self._settings.set('_enabled', False)
            self.enabled = False
            self._plugin.disable()


class BrokenPlugin(_PluginConnector):

    def __init__(self, error, plugin_class):
        name = utils.name_from_class(plugin_class, 'Plugin')
        doc = 'This plugin is disabled because it failed to load properly.\n' \
               + 'Error: ' + error
        _PluginConnector.__init__(self, name, doc=doc, error=error)
        LOG.error("Taking %s plugin into use failed:\n%s" % (name, error))

    def enable_on_startup(self):
        pass
