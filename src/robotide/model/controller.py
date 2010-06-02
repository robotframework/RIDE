class _Dirty(object):
    @property
    def dirty(self):
        return False


class DataController(_Dirty):

    def __init__(self, data):
        self.data = data
        self.children = [ DataController(child) for child in data.children]
        self.setting_table = SettingTableController(data.setting_table)

    @property
    def tests(self):
        return TestCaseTableController(self.data.testcase_table)

    @property
    def keywords(self):
        return KeywordTableController(self.data.keyword_table)

    def has_been_modified_on_disk(self):
        return False


class SettingTableController(_Dirty):

    def __init__(self, table):
        self._table = table


class TestCaseTableController(_Dirty):
    def __init__(self, tctable):
        self._table = tctable
    def __iter__(self):
        return iter(TestCaseController(t) for t in self._table)


class KeywordTableController(_Dirty):
    def __init__(self, kwtable):
        self._table = kwtable
    def __iter__(self):
        return iter(KeywordController(kw) for kw in self._table)


class TestCaseController(object):
    def __init__(self, test):
        self.data = test

class KeywordController(object):
    def __init__(self, keyword):
        self.data = keyword