from robotide.ui.menu import *
import wx
from wx.lib import flatnotebook as fnb



class ProtoFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title='ProtoFrame')
        self.mb = MenuBar(self)
        self.tb = ToolBar(self)
        self.ar = ActionRegisterer(self.mb, self.tb)
        action_info = ActionInfo('File', 'Event', self.OnEvent, shortcut='Ctrl-E')
        action = self.ar.register_action(action_info)
        register_unregister_actions = [(action_info, action)]
        self.ar.register_action(ActionInfo('File', 'Register', self.OnRegister))
        self.ar.register_action(ActionInfo('File', 'Unregister', self.OnUnregister))
        self.CreateStatusBar()
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(50)
        self.nb = fnb.FlatNotebook(splitter)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
        self.actions = []
        self.nb.AddPage(ProtoPanel(self, self.nb, icon='ART_CDROM'), 'F1')
        self.actions = []
        self.nb.AddPage(ProtoPanel(self, self.nb, icon='ART_CDROM'), 'F2')
        self.nb.AddPage(ProtoPanel(self, self.nb, entry='Bar', icon='ART_FLOPPY'), 'F3')
        register_unregister_actions.extend(self.actions)
        self.nb.AddPage(ProtoPanel(self, self.nb, menu='X', entry='Bar'), 'F4')
        self.nb.AddPage(ProtoPanel(self, self.nb, entry='D', scut='Del'), 'D1')
        self.nb.AddPage(ProtoPanel(self, self.nb, entry='D', scut='Del',
                                   container=False, icon='ART_ERROR'), 'D2')
        splitter.SplitVertically(Tree(splitter), self.nb, 100)
        self.actions = register_unregister_actions

    def OnPageChanging(self, event):
        newindex = event.GetSelection()
        if newindex <= self.nb.GetPageCount() - 1:
            self.nb.GetPage(newindex).SetFocus()

    def register_action(self, menu, name, action, container=None,
                        shortcut=None, icon=None, doc=''):
        a_info = ActionInfo(menu, name, action, container, shortcut, icon, doc)
        action = self.ar.register_action(a_info)
        self.actions.append((a_info, action))

    def OnUnregister(self, event):
        for i, action in self.actions:
            action.unregister()

    def OnRegister(self, event):
        actions = []
        for info, a in self.actions:
            action = self.ar.register_action(info)
            actions.append((info, action))
        self.actions = actions

    def OnEvent(self, event):
        wx.MessageBox('Main frame')


class Tree(wx.TreeCtrl):

    def __init__(self, parent):
        wx.TreeCtrl.__init__(self, parent)
        root = self.AddRoot('root')
        self.AppendItem(root, 'Foo')


class ProtoPanel(wx.Panel):
    counter = 0

    def __init__(self, frame, parent, menu='Edit', entry='Foo', scut='Ctrl-F',
                 container=True, icon=None):
        ProtoPanel.counter += 1
        name = 'Panel %d' % ProtoPanel.counter
        wx.Panel.__init__(self, parent, name=name)
        container = container and self or None
        frame.register_action(menu, entry, lambda x: wx.MessageBox(name), 
                              container, scut, icon, 'Doc for '+name)
        frame.register_action(menu, entry+' (2)', 
                              lambda x: wx.MessageBox(name+' (2)'), 
                              container, None, icon, 'Doc 2 for '+name)
        wx.TextCtrl(self, value=name)


if __name__ == '__main__':
    app = wx.PySimpleApp()
    ProtoFrame().Show()
    app.MainLoop()
