# IDBS Training Application Plugin UI
#
# Steve Jefferies
#

import wx
import atexit
import sys
import os
import subprocess

import wx.lib.agw.hyperlink as hl
from robotide.widgets import VerticalSizer

class ApplicationRunner(wx.Panel):

    def __init__(self, parent, notebook):
        self._notebook = notebook
        self._application_process = None
        title = "Training Application Controls"
        sys.api_version
        wx.Panel.__init__(self, notebook)
        self._parent = parent
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(main_sizer)
        self._panel = self._notebook.AddPage(self._add_application_control(), title)

    def _add_application_control(self):
        self.panel = wx.Panel(self._notebook)
        self.panel.SetSizer(VerticalSizer())
        header_line = wx.BoxSizer(wx.HORIZONTAL)
        app_header = wx.StaticText(self.panel, label="Introduction to Test Automation Training Application")
        header_line.Add(app_header)

        control_line = wx.BoxSizer(wx.HORIZONTAL)
        self.start_button = wx.Button(self.panel, label='Launch Training Application')
        self.start_button.Bind(wx.EVT_BUTTON, self.OnApplicationLaunch)
        self.stop_button = wx.Button(self.panel, label='Stop Training Application')
        self.stop_button.Disable()
        self.stop_button.Bind(wx.EVT_BUTTON, self.OnApplicationStop)
        control_line.Add(self.start_button)
        control_line.Add(self.stop_button)

        self.status_line = wx.BoxSizer(wx.HORIZONTAL)
        self.status_field = wx.StaticText(self.panel, label='Training Application Not Running')
        self.status_line.Add(self.status_field)
        self.hyper1 = hl.HyperLinkCtrl(self.panel, wx.ID_ANY, "http://localhost:8080", URL="http://localhost:8080")
        self.status_line.Add(self.hyper1)
        self.status_line.Hide(self.hyper1)
        
        self.link_line = wx.BoxSizer(wx.HORIZONTAL)

        self.panel.Sizer.Add(header_line, 0, wx.ALL, 3)
        self.panel.Sizer.Add(control_line, 0, wx.ALL, 3)
        self.panel.Sizer.Add(self.status_line, 0, wx.ALL, 3)
        self.panel.Sizer.Add(self.link_line, 0, wx.ALL, 3)

        return self.panel

    def OnApplicationLaunch(self, event):
        application_path = os.path.dirname(os.path.abspath(__file__)) + "/app/training_web_app/tasks/tasks.py"
        self._application_process = subprocess.Popen('python "{0}"'.format(application_path), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        atexit.register(self.cleanup_training_application, self._application_process)
        self.start_button.Disable()
        self.stop_button.Enable()
        self.status_field.SetLabel("Training Application Running at: ")
        self.status_line.Show(self.hyper1)
        self.status_line.Layout()

    def OnApplicationStop(self, event):
        if self._application_process:
            self._application_process.kill()
            self._application_process = None
            atexit.register(self.cleanup_training_application, None)
        self.start_button.Enable()
        self.stop_button.Disable()
        self.status_field.SetLabel("Training Application Not Running")
        self.status_line.Hide(self.hyper1)

    def cleanup_training_application(self, proc):
        if proc:
            proc.kill()
