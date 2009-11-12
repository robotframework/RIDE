import wx
from wx.lib import flatnotebook as fnb

from menu import *


class ProtoFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title='ProtoFrame')
        self.mb = MenuBar(self)
        self.mb.register_menu_entry(MenuEntry('File', 'Event', self.OnEvent,
                                              shortcut='Alt-e'))
        self.SetMenuBar(self.mb)
        self.CreateStatusBar()
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(50)
        self.nb = fnb.FlatNotebook(splitter)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
        self.nb.AddPage(ProtoPanel(self, self.nb), 'P1')
        self.nb.AddPage(ProtoPanel(self, self.nb), 'P2')
        self.nb.AddPage(ProtoPanel(self, self.nb, scut='Del'), 'P3')
        self.nb.AddPage(ProtoPanel(self, self.nb, entry='Bar'), 'P4')
        self.nb.AddPage(ProtoPanel(self, self.nb, menu='X', entry='Bar'), 'P5')
        splitter.SplitVertically(Tree(splitter), self.nb, 100)

    def OnPageChanging(self, event):
        newindex = event.GetSelection()
        if newindex <= self.nb.GetPageCount() - 1:
            self.nb.GetPage(newindex).SetFocus()

    def register_menu_entry(self, menu, name, action, container=None,
                            shortcut=None, doc=''):
        self.mb.register_menu_entry(MenuEntry(menu, name, action, container,
                                              shortcut, doc))

    def OnEvent(self):
        wx.MessageBox('Main frame')


class Tree(wx.TreeCtrl):

    def __init__(self, parent):
        wx.TreeCtrl.__init__(self, parent)
        root = self.AddRoot('root')
        self.AppendItem(root, 'Foo')


class ProtoPanel(wx.Panel):
    counter = 0

    def __init__(self, frame, parent, menu='Edit', entry='Foo', scut='Ctrl-F'):
        wx.Panel.__init__(self, parent)
        ProtoPanel.counter += 1
        name = 'Panel %d' % ProtoPanel.counter
        frame.register_menu_entry(menu, entry, lambda: wx.MessageBox(name), 
                                  self, scut, 'Doc for '+name)
        wx.TextCtrl(self, value=name)


if __name__ == '__main__':
    app = wx.PySimpleApp()
    ProtoFrame().Show()
    app.MainLoop()
