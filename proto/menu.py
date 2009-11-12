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

    def __init__(self, menu, name, action, container=None, shortcut=None, doc=''):
        self.id = wx.NewId()
        self.menu = menu
        self.name = self._get_name(name, shortcut)
        self.doc = doc
        self.action = ActionFactory(self, action, container)

    def _get_name(self, name, shortcut):
        if shortcut:
            return '%s\t%s' % (name, shortcut)
        return name

    def register(self, menu, frame):
        if self._is_not_registered(menu):
            menu.Append(self.id, self.name, self.doc)
        frame.Bind(wx.EVT_MENU, self.action, id=self.id)

    def _is_not_registered(self, menu):
        id = menu.FindItem(self.name)
        if id == -1:
            return True
        return menu.FindItemById(id).GetItemLabel() != self.name


ACTIONS = {}

def ActionFactory(entry, action, container):
    proxy = ACTIONS.setdefault((entry.menu, entry.name), ActionProxy())
    proxy.register_action(Actor(action, container))
    return proxy


class ActionProxy(object):

    def __init__(self):
        self._actions = []

    def register_action(self, action):
        self._actions.append(action)

    def __call__(self, event):
        for actor in self._actions:
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
