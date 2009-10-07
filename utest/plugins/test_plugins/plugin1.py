from robotide.application.plugin import Plugin

def init_plugin(frame):
    return ExamplePlugin(frame)

class ExamplePlugin(Plugin):
    def __init__(self, app=None):
        self.active = False
        self.name = "Test Plugin 1"
        self.id = "test.plugin1"

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False


