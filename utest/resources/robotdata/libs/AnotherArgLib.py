class AnotherArgLib(object):

    def __init__(self, *args):
        self._check_args(args)
        self._args = args

    def _check_args(self, args):
        for arg in args:
            if arg and '${' in arg:
                raise ValueError('Test library needs variables resolved')

    def longest(self):
        return max(self._args, key=len)
