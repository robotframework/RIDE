from robot.api.deco import keyword as keyword

ROBOT_LIBRARY_DOC_FORMAT = 'REST'

"""
.. code:: robotframework
    *** Test Cases ***
        Example
            pretty rest keyword # How cool is this!!?!!?!1!!
"""

def rest_doc_keyword1():
    """ 
    **doc_format**
    *reST*
    """
    return True


@keyword("pretty rest keyword")
def rest_doc_keyword2(arg1, arg2='default value', *args):
    """reST documentaion
    """
    pass
