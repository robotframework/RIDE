from robot.api.deco import keyword as keyword

ROBOT_LIBRARY_DOC_FORMAT = 'ROBOT'

"""
_Simple_ *robot* _library_
"""

def robot_doc_keyword1():
    """ 
    = doc_format =
    - robot
    """
    pass


@keyword("pretty robot keyword")
def robot_doc_keyword2(arg1, arg2='default value', *args):
    """robot documentaion
    """
    pass
