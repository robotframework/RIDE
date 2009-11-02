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

from robotide.context import SETTINGS, LOG
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
        self.config_panel = lambda self: None


class PluginConnector(_PluginConnector):

    def __init__(self, application, plugin):
        _PluginConnector.__init__(self, plugin.name, plugin.doc)
        self.config_panel = plugin.config_panel
        self.activate = plugin.activate
        self.deactivate = plugin.deactivate
        if SETTINGS['plugins'].get(plugin.name, plugin.initially_active):
            plugin.activate()
            self.active = True


class BrokenPlugin(_PluginConnector):

    def __init__(self, error, plugin_class):
        name = utils.name_from_class(plugin_class, 'Plugin')
        _PluginConnector.__init__(self, name, error=error)
        LOG.error("Taking %s plugin into use failed:\n%s" % (name, error))

