import wx


class MenuBar(wx.MenuBar):

    def __init__(self, frame):
        wx.MenuBar.__init__(self)
        self._frame = frame

    def register_menu_entry(self, entry):
        menu = self._get_or_create_menu(entry.menu)
        entry.bind_to_menu(menu, self._frame)

    def _get_or_create_menu(self, name):
        position = self.FindMenu(name)
        if position == -1:
            self.Append(wx.Menu(), name)
            position = self.FindMenu(name)
        return self.GetMenu(position)


class MenuEntry(object):
    _actions = {}

    def __init__(self, menu, name, action, container=None, 
                 shortcut=None, doc=''):
        self.id = wx.NewId()
        self.menu = menu
        self.name = shortcut and '%s\t%s' % (name, shortcut) or name
        self.doc = doc
        self.action = self._register_entry(shortcut, action, container)

    def _register_entry(self, shortcut, action, container):
        key = shortcut or (self.menu, self.name)
        delegator = self._actions.setdefault(key, ActionDelegator())
        delegator.add(action, container)
        return delegator

    def bind_to_menu(self, menu, frame):
        if self._is_not_bound_to_menu(menu):
            menu.Append(self.id, self.name, self.doc)
            frame.Bind(wx.EVT_MENU, self.action, id=self.id)

    def _is_not_bound_to_menu(self, menu):
        id = menu.FindItem(self.name)
        if id == -1:
            return True
        return menu.FindItemById(id).GetItemLabel() != self.name


class ActionDelegator(object):

    def __init__(self):
        self._actors = []

    def add(self, action, container):
        self._actors.append(Actor(action, container))

    def __call__(self, event):
        for actor in self._actors:
            actor.act()


class Actor(object):

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
