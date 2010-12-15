from robotide import utils

class CellInfo(object):

    def __init__(self, content_type, cell_type, cell_value):
        self._content_type = content_type
        self._cell_type = cell_type
        self._cell_value = cell_value

    @property
    def content_type(self):
        return self._content_type

    @property
    def cell_type(self):
        return self._cell_type

    def has_error(self):
        if self.cell_type is CellType.MANDATORY \
            and self.content_type in [ContentType.EMPTY, ContentType.COMMENTED]:
            return True
        if self.cell_type is CellType.MANDATORY_EMPTY \
            and self.content_type not in [ContentType.EMPTY, ContentType.COMMENTED]:
            return True
        return False

    def matches(self, value):
        if not value or not self._cell_value:
            return False
        selection = utils.normalize(value, ignore=['_'])
        if not selection:
            return False
        cell = utils.normalize(self._cell_value, ignore=['_'])
        if not cell:
            return False
        if selection == cell:
            return True
        return self._variable_matches(selection, cell)

    def _variable_matches(self, selection, cell):
        variable = utils.get_variable_basename(selection)
        if not variable:
            return False
        variables = utils.find_variable_basenames(cell)
        if variable in variables:
            return True
        return self._list_variable_used_as_scalar(variable, variables)

    def _list_variable_used_as_scalar(self, variable, variables):
        return '$%s' % variable[1:] in variables


class ContentType:
    USER_KEYWORD = 'USER_KEYWORD'
    LIBRARY_KEYWORD = 'LIBRARY_KEYWORD'
    VARIABLE = 'VARIABLE'
    COMMENTED = 'COMMENTED'
    STRING = 'STRING'
    EMPTY = 'EMPTY'


class CellType:
    KEYWORD = 'KEYWORD'
    MANDATORY = 'MANDATORY'
    OPTIONAL = 'OPTIONAL'
    UNKNOWN = 'UNKNOWN'
    MANDATORY_EMPTY = 'MANDATORY_EMPTY'