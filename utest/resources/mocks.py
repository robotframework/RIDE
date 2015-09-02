from robotide.preferences.settings import Settings
from robotide.preferences.excludes import Excludes
from robotide.publish import PUBLISHER


class MessageRecordingLoadObserver(object):
    def __init__(self):
        self._log = ''
        self.finished = False
        self.notified = False

    def notify(self):
        if self.finished:
            raise RuntimeError('Notified after finished')
        self.notified = True

    def finish(self):
        self.finished = True

    def error(self, msg):
        if self.finished:
            raise RuntimeError('Errored after finished')
        self.finish()
        self._log = msg

    @property
    def message(self):
        return self._log


class _FakeModel(object):
    suite = None


class _FakeActions(object):
    def register_action(self, *args):
        return self

    def unregister(self, *args):
        pass


class _FakeUIObject(object):
    Enable = InsertSeparator = Append = Connect = lambda *args: None
    Insert = FindMenu = GetMenuBar = GetMenu = lambda *args: _FakeUIObject()
    GetMenuItemCount = lambda s: 1
    notebook = property(lambda *args: _FakeUIObject())
    actions = property(lambda *args: _FakeActions())


class FakeSettings(Settings):
    def __init__(self, settings=None):
        Settings.__init__(self, None)
        self.add_section('Plugins')
        self.set('pythonpath', [])
        self.set('auto imports', [])
        if settings:
            for key, val in settings.items():
                self.set(key, val)


class FakeApplication(object):
    frame = _FakeUIObject()
    model = _FakeModel()
    namespace = None
    get_model = lambda s: _FakeModel()
    subscribe = lambda s, x, y: None
    get_menu_bar = lambda s: _FakeUIObject()
    get_notebook = lambda s: _FakeUIObject()
    get_frame = lambda s: _FakeUIObject()
    create_menu_item = lambda *args: None
    settings = FakeSettings()


class _FakeSetting(object):
    add_section = lambda self, name: _FakeSetting()
    get = lambda self, name, default: True
    set = lambda self, name, value: None


class PublisherListener(object):

    def __init__(self, topic):
        PUBLISHER.subscribe(self._listener, topic, self)
        self._topic = topic
        self.data = []
        self.outer_listener = lambda message: 0

    def _listener(self, data):
        self.data.append(data)
        self.outer_listener(data)

    @property
    def count(self):
        return len(self.data)

    def unsubscribe(self):
        PUBLISHER.unsubscribe(self._listener, self._topic, self)
