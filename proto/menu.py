import wx


class MenuBar(wx.MenuBar):

    def __init__(self, frame):
        wx.MenuBar.__init__(self)
        self._frame = frame

    def register_menu_entry(self, entry):
        menu = self._get_or_create_menu(entry.menu)
        entry.register(menu, self._frame)

    def _get_or_create_menu(self, name):
        position = self.FindMenu(name)
        if position == -1:
            self.Append(wx.Menu(), name)
            position = self.FindMenu(name)
        return self.GetMenu(position)


class MenuEntry(object):
    _actions = {}

    def __init__(self, menu, name, action, container=None, shortcut=None, doc=''):
        self.id = wx.NewId()
        self.menu = menu
        self.name = self._get_name(name, shortcut)
        self.doc = doc
        self.action = self._get_action(action, container)

    def _get_name(self, name, shortcut):
        if shortcut:
            return '%s\t%s' % (name, shortcut)
        return name

    def _get_action(self, action, container):
        delegator = self._actions.setdefault((self.menu, self.name),
                                             ActionDelegator())
        delegator.add(action, container)
        return delegator

    def register(self, menu, frame):
        if self._is_not_registered(menu):
            menu.Append(self.id, self.name, self.doc)
            frame.Bind(wx.EVT_MENU, self.action, id=self.id)

    def _is_not_registered(self, menu):
        id = menu.FindItem(self.name)
        if id == -1:
            return True
        return menu.FindItemById(id).GetItemLabel() != self.name


class ActionDelegator(object):

    def __init__(self):
        self._actions = []

    def add(self, action, container):
        self._actions.append(Action(action, container))

    def __call__(self, event):
        for action in self._actions:
            action.act()


class Action(object):

    def __init__(self, action, container):
        self._action = action
        self._container = container

    def act(self):
        if self._should_act():
            self._action()

    def _should_act(self):
        if self._container is None:
            return True
        if not self._container.IsShownOnScreen():
            return False
        widget = wx.GetActiveWindow()
        while widget:
            if widget == self._container.Parent:
                return True
            widget = widget.GetParent()
        return False
