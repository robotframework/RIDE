class ArgLib(object):

    def __init__(self, mandatory_arg, default_arg=None):
        self._check_args((mandatory_arg, default_arg))
        self._mandatory = mandatory_arg
        self._default =default_arg

    def _check_args(self, args):
        for arg in args:
            if arg and '${' in arg:
                raise ValueError('Test library needs variables resolved')

    def get_mandatory(self):
        return self._mandatory

    def get_default(self):
        if not self._default:
            raise AssertionError("Default not properly set!")
        return self._default
