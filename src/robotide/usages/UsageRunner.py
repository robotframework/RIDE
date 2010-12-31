from robotide.usages.commands import FindUsages
from robotide.usages.usagesdialog import UsagesDialog
from threading import Thread
import wx
import time

class Usages():

    def __init__(self, controller, highlight):
        self._name = controller.name
        self._controller = controller
        self._highlight = highlight
        self._dlg = UsagesDialog(self._name)
        self._worker = Thread(target=self._run)
        self._dialog_closed = False

    def show(self):
        self._dlg.add_selection_listener(self._highlight)
        self._dlg.Bind(wx.EVT_CLOSE, self._stop)
        self._dlg.Show()
        self._worker.start()

    def _run(self):
        wx.CallAfter(self._dlg.begin_searching)
        for usage in self._controller.execute(FindUsages(self._name)):
            time.sleep(0) # GIVE SPACE TO OTHER TRHEADS -- Thread.yield in Java
            if self._dialog_closed: return
            wx.CallAfter(self._dlg.add_usage, usage)
        wx.CallAfter(self._dlg.end_searching)

    def _begin_search(self):
        if not self._dialog_closed:
            self._dlg.begin_searching()

    def _add_usage(self, usage):
        if not self._dialog_closed:
            self._dlg.add_usage(usage)

    def _end_search(self):
        if not self._dialog_closed:
            self._dlg.end_searching()

    def _stop(self, event):
        self._dialog_closed = True
        event.Skip()