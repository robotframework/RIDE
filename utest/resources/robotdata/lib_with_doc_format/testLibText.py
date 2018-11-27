from robot.api.deco import keyword as keyword

ROBOT_LIBRARY_DOC_FORMAT = 'TEXT'

"""
Simple text library
"""

def text_doc_keyword1():
    """ 
    doc_format
    text
    """
    pass


@keyword("pretty text keyword")
def text_doc_keyword2(arg1, arg2='default value', *args):
    """text documentaion
    """
    pass
