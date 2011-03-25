class Tag(object):
    tooltip = "Test case's tag"

    def __init__(self, name, index=None, controller=None):
        self._name = name
        self._index = index
        self._controller = controller

    @property
    def name(self):
        return self._name

    @property
    def controller(self):
        return self._controller

    def set_index(self, index):
        self._index = index

    def is_empty(self):
        return self.name is None

    def __eq__(self, other):
        return self._name == other._name and self._index == other._index

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return self._name

    def choose(self, mapping):
        return mapping[self.__class__]


class ForcedTag(Tag):
    tooltip = "Force tag"


class DefaultTag(Tag):
    tooltip = "Default tag"
