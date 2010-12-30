from robotide.controller.commands import FindUsages
from robotide.usages.usagesdialog import UsagesDialog
from threading import Thread
import wx
import time

class Usages(Thread):

    def __init__(self, controller, highlight):
        Thread.__init__(self)
        self._name = controller.name
        self._controller = controller
        self._highlight = highlight
        self._dlg = UsagesDialog(self._name)

    def run(self):
        wx.CallAfter(self._dlg.begin_searching)
        for usage in self._controller.execute(FindUsages(self._name)):
            time.sleep(0) # GIVE SPACE TO OTHER TRHEADS -- Thread.yield in Java
            wx.CallAfter(self._dlg.add_usage, usage)
        wx.CallAfter(self._dlg.end_searching)

    def show(self):
        self._dlg.add_selection_listener(self._highlight)
        self._dlg.Show()
        self.start()