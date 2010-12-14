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
        # TODO: refactor
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
        match = utils.match_variable(selection)
        if match:
            if match.groups()[0] in cell:
                return True
            vars = utils.find_variable_basenames(cell)
            if vars:
                for var_basename in vars:
                    if var_basename == match.groups()[1]:
                        return True
        return False


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