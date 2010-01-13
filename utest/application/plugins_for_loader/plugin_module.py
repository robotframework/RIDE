from robotide.pluginapi import Plugin


class ExamplePlugin1(Plugin):

    def __init__(self, application):
        Plugin.__init__(self, application)


class ExamplePlugin2(Plugin):

    def __init__(self, application):
        Plugin.__init__(self, application)

    def turn_off(self, name):
        self._get_plugin_by_name(name).disable()

    def _get_plugin_by_name(self, name):
        for p in self.get_plugins():
            if p.name == name:
                return p
        return None
