class Tag(object):

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def __eq__(self, other):
        return self._name == other._name

    def __str__(self):
        return self._name


class ForcedTag(Tag):
    pass

class DefaultTag(Tag):
    pass