from robotide.event import RideMessage


class _FakeModel(object):
    suite = None

class _FakeUIObject(object):
    Enable = InsertSeparator = Append = Connect = lambda *args: None
    Insert = FindMenu = GetMenuBar = GetMenu = lambda *args: _FakeUIObject()
    GetMenuItemCount = lambda s: 1
    notebook = property(lambda *args: _FakeUIObject())

class FakeApplication(object):
    frame = _FakeUIObject()
    model = _FakeModel()
    get_model = lambda s: _FakeModel()
    subscribe = lambda s, x, y: None
    get_menu_bar = lambda s: _FakeUIObject()
    get_notebook = lambda s: _FakeUIObject()
    get_frame = lambda s: _FakeUIObject()
    create_menu_item = lambda *args: None


class RideTestMessage(RideMessage):
    pass

class RideMessageWithData(RideMessage):
    data = ['data_item', 'more_data']
