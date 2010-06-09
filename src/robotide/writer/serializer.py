from robotide.writer.writer import FileWriter


class Serializer(object):

    def __init__(self, output=None):
        self._output = output
        self.table_handlers = {'setting': self.setting_table_handler, 
                               'variable': self.variable_table_handler,
                               'keyword': self.keyword_table_handler,
                               'testcase': self.testcase_table_handler}

    def serialize(self, datafile):
        writer = FileWriter(datafile.source, self._output)
        for table in datafile:
            if table:
                self.table_handlers[table.type](writer, table)

    def setting_table_handler(self, writer, table):
        writer.start_settings()
        for setting in table:
            if setting.is_set():
                setting_list = setting.as_list()
                writer.element(setting_list, comment=setting.comment)
        writer.end_settings()

    def variable_table_handler(self, writer, table):
        writer.start_variables()
        for var in table:
            writer.element([var.name]+var.value, comment=var.comment)
        writer.end_variables()

    def keyword_table_handler(self, writer, table):
        writer.start_keywords()
        for kw in table:
            self.handle_keyword(writer, kw)
        writer.end_keywords()

    def handle_keyword(self, writer, kw):
        writer.start_keyword(kw)
        for step in kw:
            if step.is_set():
                writer.element(step.as_list(), comment=step.comment)
        writer.end_keyword()

    def testcase_table_handler(self, writer, table):
        writer.start_testcases()
        for tc in table:
            self.handle_testcase(writer, tc)
        writer.end_testcases()

    def handle_testcase(self, writer, tc):
        writer.start_testcase(tc)
        for step in tc:
            if step.is_set():
                writer.element(step.as_list(), comment=step.comment)
        writer.end_testcase()
