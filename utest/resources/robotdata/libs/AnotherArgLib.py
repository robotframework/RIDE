class AnotherArgLib(object):

    def __init__(self, some, arguments, to, library):
        self._args = [some, arguments, to, library]

    def longest(self):
        return max(self._args, key=len)
