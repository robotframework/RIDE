from robotide.application.plugin import Plugin

def init_plugin(frame):
    return ExamplePlugin(frame)

class ExamplePlugin(Plugin):
    def __init__(self, app=None):
        self.active = True
        self.name = "Test Plugin 2"
        self.id = "test.plugin2"

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False


