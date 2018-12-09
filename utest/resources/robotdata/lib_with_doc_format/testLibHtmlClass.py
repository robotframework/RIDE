from robot.api.deco import keyword as keyword

class testLibHtmlClass:
    ROBOT_LIBRARY_DOC_FORMAT = 'HTML'

    """
    <h1>Class</h1>
    <b>HTML</b>
    <i>library</i>
    """

    def html_doc_keyword1(self):
        """ 
        <b> doc_format </b>
        <i> html </i>
        """
        pass

    @keyword("pretty html keyword")
    def html_doc_keyword2(self, arg1, arg2='default value', *args):
        """<i><b>html</b> documentaion </i>
        """
        pass
