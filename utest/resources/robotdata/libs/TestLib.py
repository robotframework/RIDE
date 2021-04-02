def testlib_keyword():
    """
    """
    return True


def testlib_keyword_with_args(arg1, arg2='default value', *args):
    """This keyword requires one argument, has one optional argument and varargs.

    This is some more documentation
    """
    pass

def testlib_keyword_with_kwonlyargs(arg1, *args, namedarg1, namedarg2='default value', **kwargs):
    pass
