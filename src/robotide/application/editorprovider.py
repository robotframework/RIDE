class EditorProvider(object):

    def __init__(self):
        self._editors = {}

    def register_editor(self, key, editor, default=True):
        if key not in self._editors:
            self._editors[key] = _EditorList()
        self._editors[key].add(editor, default)

    def unregister_editor(self, key, editor):
        self._editors[key].remove(editor)

    def set_editor(self, key, editor):
        self._editors[key].set_default(editor)

    def get_editor(self, key):
        return self._editors[key].get()

    def get_editors(self, key):
        return self._editors[key].get_all()


class _EditorList(object):

    def __init__(self):
        self._editors = []

    def add(self, editor, default=True):
        if editor in self._editors:
            return
        if default:
            self._editors.append(editor)
        else:
            self._editors.insert(0, editor)

    def set_default(self, editor):
        if not self._editors.index(editor) == -1:
            self._editors.remove(editor)
            self._editors.append(editor)

    def remove(self, editor):
        self._editors.remove(editor)

    def get(self):
        return self._editors[-1]

    def get_all(self):
        return self._editors
