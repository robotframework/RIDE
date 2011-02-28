class Tag(object):

    def __init__(self, name, controller):
        self._name = name
        self._controller = controller

    @property
    def name(self):
        return self._name

    @property
    def controller(self):
        return self._controller

    def __eq__(self, other):
        return self._name == other._name

    def __str__(self):
        return self._name

    def choose(self, mapping):
        return mapping[self.__class__]

class ForcedTag(Tag):
    pass

class DefaultTag(Tag):
    pass