from robot.api.deco import keyword as keyword

ROBOT_LIBRARY_DOC_FORMAT = 'HTML'

"""
Simple html library
"""

def html_doc_keyword1():
    """ 
    <b> doc_format </b>
    <i> html </i>
    """
    pass


@keyword("pretty html keyword")
def html_doc_keyword2(arg1, arg2='default value', *args):
    """<i><b>html</b> documentaion </i>
    """
    pass
