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
                writer.setting(setting_list[0], setting_list[1:], comment=setting.comment)
        writer.end_settings()

    def variable_table_handler(self, writer, table):
        writer.start_variables()
        for var in table:
            writer.variable(var.name, var.value, comment=var.comment)
        writer.end_variables()

    def keyword_table_handler(self, writer, table):
        writer.start_keywords()
        for kw in table:
            self.handle_keyword(writer, kw)
        writer.end_keywords()

    def handle_keyword(self, writer, kw):
        writer.start_keyword(kw)
        for step in kw.steps:
            writer.keyword(step.as_list(), comment=step.comment)
        writer.end_keyword()

    def testcase_table_handler(self, writer, table):
        self._output.write('testcase')
