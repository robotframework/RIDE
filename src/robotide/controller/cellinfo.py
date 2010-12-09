class CellInfo(object):

    def __init__(self, content_type, cell_type):
        self._content_type = content_type
        self._cell_type = cell_type

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


class ContentType:
    USER_KEYWORD = object()
    LIBRARY_KEYWORD = object()
    VARIABLE = object()
    COMMENTED = object()
    STRING = object()
    EMPTY = object()


class CellType:
    MANDATORY = object()
    OPTIONAL = object()
    UNKNOWN = object()
    MANDATORY_EMPTY = object()