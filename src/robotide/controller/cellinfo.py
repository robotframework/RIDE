from robotide import utils


class CellInfo(object):

    def __init__(self, content_type, cell_type, cell_value, arg_name, source, for_loop=False):
        self._content_type = content_type
        self._cell_type = cell_type
        self._cell_value = cell_value
        self.arg_name = arg_name
        self.source = source
        self.for_loop = for_loop

    @property
    def content_type(self):
        return self._content_type

    @property
    def cell_type(self):
        return self._cell_type

    def has_error(self):
        return self.argument_missing() or self.too_many_arguments()

    def argument_missing(self):
        return self.cell_type == CellType.MANDATORY \
            and self.content_type in [ContentType.EMPTY, ContentType.COMMENTED]

    def too_many_arguments(self):
        return self.cell_type == CellType.MUST_BE_EMPTY \
            and self.content_type not in [ContentType.EMPTY, ContentType.COMMENTED]

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


def TipMessage(cell):
    if cell.for_loop:
        return _ForLoopTooltipMessage(cell)
    return _TooltipMessage(cell)


class _TooltipMessage(object):

    def __init__(self, cell):
        self.message = self._get_message(cell)

    def _get_message(self, cell):
        handlers = {
            CellType.ASSIGN: self._assign,
            CellType.KEYWORD: self._keyword,
            CellType.MANDATORY: self._mandatory,
            CellType.OPTIONAL: self._optional,
            CellType.MUST_BE_EMPTY: self._must_be_empty,
            CellType.UNKNOWN: self._unknown,
        }
        return handlers[cell.cell_type](cell)

    def _must_be_empty(self, cell):
        if cell.too_many_arguments():
            return "Too many arguments"
        return ''

    def _mandatory(self, cell):
        if cell.argument_missing():
            return "Missing argument:  %s" % cell.arg_name
        return "Argument:  %s" % cell.arg_name

    def _optional(self, cell):
        return "Optional argument:  %s" % cell.arg_name

    def _keyword(self, cell):
        if cell.content_type == ContentType.STRING:
            return "Keyword not found"
        if cell.content_type in ContentType.KEYWORDS:
            return "Keyword from:  %s\n\nPress <ctrl> for details" % cell.source
        return ''

    def _assign(self, cell):
        return 'Variable assignment'

    def _unknown(self, cell):
        return ''

    def __nonzero__(self):
        return bool(self.message)

    def __str__(self):
        return self.message


class _ForLoopTooltipMessage(_TooltipMessage):

    def _get_message(self, cell):
        if cell.too_many_arguments():
            return "Too many parameters in for loop"
        return ''


class ContentType:
    USER_KEYWORD = 'USER_KEYWORD'
    LIBRARY_KEYWORD = 'LIBRARY_KEYWORD'
    KEYWORDS = (USER_KEYWORD, LIBRARY_KEYWORD)
    VARIABLE = 'VARIABLE'
    COMMENTED = 'COMMENTED'
    STRING = 'STRING'
    EMPTY = 'EMPTY'


class CellType:
    ASSIGN = 'ASSIGN'
    KEYWORD = 'KEYWORD'
    MANDATORY = 'MANDATORY'
    OPTIONAL = 'OPTIONAL'
    MUST_BE_EMPTY = 'MUST_BE_EMPTY'
    UNKNOWN = 'UNKNOWN'
