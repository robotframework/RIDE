class FakePlugin(object):
    def __init__(self, editors, item):
        self._editors = editors
        self._item = item

    def get_selected_item(self):
        return self._item

    def get_editor(self, itemclass):
        return self._editors[itemclass]

    def subscribe(self, *args):
        pass

    def unsubscribe(self, *args):
        pass
