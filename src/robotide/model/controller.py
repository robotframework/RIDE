from robotide.robotapi import TestCaseFile
from robotide.editor.editors import DocumentationEditor, SettingEditor


def DataController(data):
    return TestCaseFileController(data) if isinstance(data, TestCaseFile) \
        else TestDataDirectoryController(data)


class _Dirty(object):
    @property
    def dirty(self):
        return False


class _DataController(_Dirty):

    @property
    def settings(self):
        return self._settings()

    def _settings(self):
        ss = self.data.setting_table
        return [DocumentationController(ss.doc),
                FixtureController(ss.suite_setup, 'Suite Setup'),
                FixtureController(ss.suite_teardown, 'Suite Teardown'),
                FixtureController(ss.test_setup, 'Test Setup'),
                FixtureController(ss.test_teardown, 'Test Teardown'),
                TagsController(ss.force_tags, 'Force Tags'),
                ]

    @property
    def variables(self):
        return VariableTableController(self.data.variable_table)

    @property
    def tests(self):
        return TestCaseTableController(self.data.testcase_table)

    @property
    def keywords(self):
        return KeywordTableController(self.data.keyword_table)

    @property
    def imports(self):
        return ImportSettingsController(self.data.setting_table)

    @property
    def metadata(self):
        return MetadataListController(self.data.setting_table)

    def has_been_modified_on_disk(self):
        return False


class TestDataDirectoryController(_DataController):

    def __init__(self, data):
        self.data = data
        self.children = [DataController(child) for child in data.children]


class TestCaseFileController(_DataController):

    def __init__(self, data):
        self.data = data
        self.children = []

    def _settings(self):
        ss = self.data.setting_table
        return _DataController._settings(self) + \
                [TimeoutController(ss.test_timeout, 'Test Timeout'),
                 TemplateController(ss.test_template, 'Test Template')]


class VariableTableController(_Dirty):
    def __init__(self, variables):
        self._variables = variables
    def __iter__(self):
        return iter(VariableController(v) for v in self._variables)
    @property
    def parent(self):
        return self._variables.parent


class VariableController(object):
    def __init__(self, var):
        self._var = var
        self.name = var.name
        self.value= var.value


class MetadataListController(_Dirty):
    def __init__(self, setting_table):
        self._table = setting_table
    def __iter__(self):
        return iter(MetadataController(m) for m in self._table.metadata)
    @property
    def parent(self):
        return self._table.parent


class MetadataController(object):
    def __init__(self, meta):
        self._meta = meta
        self.name = meta.name
        self.value = meta.value


class TestCaseTableController(_Dirty):
    def __init__(self, tctable):
        self._table = tctable
    def __iter__(self):
        return iter(TestCaseController(t) for t in self._table)


class TestCaseController(object):
    def __init__(self, test):
        self.data = self._test = test

    @property
    def settings(self):
        return [DocumentationController(self._test.doc),
                FixtureController(self._test.setup, 'Setup'),
                FixtureController(self._test.teardown, 'Teardown'),
                TagsController(self._test.tags, 'Tags'),
                TimeoutController(self._test.timeout, 'Timeout'),
                TemplateController(self._test.template, 'Template')]
    @property
    def name(self):
        return self._test.name

    @property
    def parent(self):
        return self._test.parent

    @property
    def steps(self):
        return self._test.steps


class KeywordTableController(_Dirty):
    def __init__(self, kwtable):
        self._table = kwtable
    def __iter__(self):
        return iter(KeywordController(kw) for kw in self._table)


class KeywordController(object):
    def __init__(self, kw):
        self.data = self._kw = kw

    @property
    def settings(self):
        return [DocumentationController(self._kw.doc),
                ArgumentsController(self._kw.args, 'Arguments'),
                TimeoutController(self._kw.timeout, 'Timeout'),
                # TODO: Wrong class, works right though
                ArgumentsController(self._kw.return_, 'Return Value')]

    @property
    def name(self):
        return self._kw.name

    @property
    def parent(self):
        return self._kw.parent

    @property
    def steps(self):
        return self._kw.steps


class ImportSettingsController(_Dirty):
    def __init__(self, setting_table):
        self._table = setting_table
    def __iter__(self):
        return iter(ImportController(imp) for imp in self._table.imports)
    @property
    def parent(self):
        return self._table.parent


class ImportController(object):
    def __init__(self, import_):
        self._import = import_
        self.type = self._import.type
        self.name = self._import.name
        self.args = self._import.args

class DocumentationController(object):
    editor = DocumentationEditor
    label = 'Documentation'
    def __init__(self, doc):
        self._doc = doc

    @property
    def parent(self):
        return self._doc.parent

    @property
    def value(self):
        return self._doc.value

    def set_value(self, value):
        self._doc.value = value


class FixtureController(object):
    editor = SettingEditor
    def __init__(self, fixture, label):
        self._fixture = fixture
        self.label = label

    @property
    def parent(self):
        return self._fixture.parent

    @property
    def value(self):
        return ' | '.join([self._fixture.name] + self._fixture.args)

    def is_set(self):
        return self._fixture.is_set()

    def set_value(self, value):
        raise NotImplementedError()


class TagsController(object):
    editor = SettingEditor
    def __init__(self, tags, label):
        self._tags = tags
        self.label = label

    @property
    def parent(self):
        return self._tags.parent

    @property
    def value(self):
        return ' | '.join(self._tags.value)

    def is_set(self):
        return self._tags.is_set()

    def set_value(self, value):
        raise NotImplementedError()


class TimeoutController(object):
    editor = SettingEditor
    def __init__(self, timeout, label):
        self._timeout = timeout
        self.label = label

    @property
    def parent(self):
        return self._timeout.parent

    @property
    def value(self):
        return ' | '.join([self._timeout.value, self._timeout.message])

    def is_set(self):
        return self._timeout.is_set()

    def set_value(self, value):
        raise NotImplementedError()


class TemplateController(object):
    editor = SettingEditor
    def __init__(self, template, label):
        self._template = template
        self.label = label

    @property
    def parent(self):
        return self._template.parent

    @property
    def value(self):
        return self._template.value

    def is_set(self):
        return self._template.is_set()

    def set_value(self, value):
        raise NotImplementedError()


class ArgumentsController(object):
    editor = SettingEditor
    def __init__(self, args, label):
        self._args = args
        self.label = label

    @property
    def parent(self):
        return self._args.parent

    @property
    def value(self):
        return ' | '.join(self._args.value)

    def is_set(self):
        return self._args.is_set()

    def set_value(self, value):
        raise NotImplementedError()
