#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import subprocess
import sys
# Configure wx uversion to allow running test app in __main__


import time
import urllib.request as urllib2
import xmlrpc.client as xmlrpclib

import psutil
import wx
from wx import Colour

from .. import version
from ..utils.versioncomparator import cmp_versions, parse_version
from ..widgets import ButtonWithHandler, HtmlWindow, RIDEDialog
from ..postinstall.__main__ import MessageDialog

_CHECK_FOR_UPDATES_SETTING = "check for updates"
_LAST_UPDATE_CHECK_SETTING = "last update check"
SPC = "  "


class UpdateNotifierController(object):

    VERSION = version.VERSION
    SECONDS_IN_WEEK = 60*60*24*7

    def __init__(self, settings):
        self._settings = settings

    def notify_update_if_needed(self, update_notification_callback, ignore_check_condition=False):
        if ignore_check_condition:
            dev_version = checking_version = True
        else:
            checking_version = self._should_check()
            dev_version = parse_version(self.VERSION).is_devrelease
        if checking_version and self._is_new_version_available():
            update_notification_callback(self._newest_version, self._download_url, self._settings)
        if checking_version and dev_version:
            upgrade_from_dev_dialog(version_installed=self.VERSION)

    def _should_check(self):
        if self._settings.get(_CHECK_FOR_UPDATES_SETTING, None) is None:
            self._settings[_CHECK_FOR_UPDATES_SETTING] = True
            return True
        return (self._settings[_CHECK_FOR_UPDATES_SETTING] and
                time.time() - self._settings.get(_LAST_UPDATE_CHECK_SETTING, 0) > self.SECONDS_IN_WEEK)

    def _is_new_version_available(self):
        self._settings[_LAST_UPDATE_CHECK_SETTING] = time.time()
        try:
            self._newest_version = self._get_newest_version()
            self._download_url = self._get_download_url(self._newest_version)
        except Exception as e:
            print(e)
            # There are many possible errors:
            #  - Timeout
            #  - Corrupted data
            #  - Server fault message
            #  - Unexpected change in dataformat
            return False
        return cmp_versions(self.VERSION, self._newest_version) == -1

    def _get_newest_version(self):
        return self._get_response(('robotframework-ride',), 'package_releases')[0]

    def _get_download_url(self, dversion):
        from time import sleep
        sleep(1)  # To avoid HTTPTooManyRequests
        return self._get_response(('robotframework-ride', dversion), 'release_data')['download_url']

    @staticmethod
    def _get_response(params, method):
        xmlparm = xmlrpclib.dumps(params, method)
        req = urllib2.Request('https://pypi.python.org/pypi', xmlparm.encode('utf-8'), {'Content-Type': 'text/xml'})
        data = urllib2.urlopen(req, timeout=1).read()
        xml = xmlrpclib.loads(data)[0][0]
        return xml


def upgrade_from_dev_dialog(version_installed):
    VERSION = None
    dev_version = urllib2.urlopen('https://raw.githubusercontent.com/robotframework/'
                                  'RIDE/master/src/robotide/version.py', timeout=1).read().decode('utf-8')
    master_code = compile(dev_version, 'version', 'exec')
    main_dict = {'VERSION': VERSION}
    exec(master_code, main_dict)  # defines VERSION
    if cmp_versions(version_installed, main_dict['VERSION']) == -1:
        # Here is the Menu Help->Upgrade insertion part, try to highlight menu # wx.CANCEL_DEFAULT
        command = sys.executable + " -m pip install -U https://github.com/robotframework/RIDE/archive/master.zip"
        _add_content_to_clipboard(command)
        if not _askyesno("Upgrade?", f"{SPC}New development version is available.{SPC}\n{SPC}You may install"
                         f" version {main_dict['VERSION']} with:\n{SPC}{command}{SPC}\n\n"
                         f"{SPC}Click OK to Upgrade now!\n{SPC}After upgrade you will see another dialog informing"
                         f" to close this RIDE instance.{SPC}\n",
                         wx.GetActiveWindow(),  no_default=True):
            return False
        else:
            do_upgrade(command)
            return True
    else:
        _askyesno("No Upgrade Available", f"{SPC}You have the latest version of RIDE.{SPC}"
                                          f"\n\n{SPC}              Have a nice day :)\n",
                  wx.GetActiveWindow())
        return False


def _askyesno(title, message, frame=None,  no_default=False):
    if frame is None:
        _ = wx.GetApp() or wx.App()
        parent = wx.Frame(None, size=(0, 0))
    else:
        parent = wx.Frame(frame, size=(0, 0))
    parent.CenterOnScreen()
    dlg = MessageDialog(parent, message, title, ttl=8, no_default=no_default)
    dlg.Fit()
    result = dlg.ShowModal() in [wx.ID_YES, wx.ID_OK]
    # print("DEBUG: updatenotifier _askyesno Result %s" % result)
    if dlg:
        dlg.Destroy()
    # parent.Destroy()
    return result


def _add_content_to_clipboard(content):
    wx.TheClipboard.Open()
    wx.TheClipboard.SetData(wx.TextDataObject(content))
    wx.TheClipboard.Close()


def do_upgrade(command):
    _add_content_to_clipboard(command)
    # print("DEBUG: Here will be the installation step.")
    my_pid = psutil.Process()
    my_pip = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = None
    count = 0
    while not result and count < 60:
        count += 1
        outs, errs = my_pip.communicate()
        # DEBUG: Add output to a notebook tab
        print(f"{outs}\n")
        if errs:
            print(f"\nERRORS: {errs}\n")
            errs = None
        result = my_pip.returncode
        if result == 0:
            break
        """ DEBUG: need to get outs line by line
        except subprocess.SubprocessError:
            my_pip.kill()
            outs, errs = my_pip.communicate()
            result = False
            # DEBUG: Add output to a notebook tab
            print(f"{outs}\n")
            print(f"{errs}\n")
        """
        time.sleep(1)
    if result != 0:
        _askyesno("Failed to Upgrade", f"{SPC}An error occurred when installing new version",
                  wx.GetActiveWindow())
        return False
    command = sys.executable + " -m robotide.__init__ --noupdatecheck"
    wx.CallLater(500, subprocess.Popen, command.split(' '), start_new_session=True)
    # Wait 10 seconds before trying to kill this process
    """ Not working well:
    wx.CallLater(10000, psutil.Process.kill, my_pid.pid)
    """
    _askyesno("Completed Upgrade", f"\n{SPC}You should close this RIDE (Process ID = {my_pid.pid}){SPC}",
              wx.GetActiveWindow())


class LocalHtmlWindow(HtmlWindow):
    def __init__(self, parent, size=(600, 400)):
        HtmlWindow.__init__(self, parent, size)
        if "gtk2" in wx.PlatformInfo or "gtk3" in wx.PlatformInfo:
            self.SetStandardFonts()

    def OnLinkClicked(self, link):  # Overrides wx method
        wx.LaunchDefaultBrowser(link.GetHref())


class UpdateDialog(RIDEDialog):

    def __init__(self, uversion, url, settings, modal=True):
        self._settings = settings
        self._command = sys.executable + f" -m pip install -U robotframework-ride=={uversion}"
        _add_content_to_clipboard(self._command)
        RIDEDialog.__init__(self, title="Update available", size=(600, 400),
                            style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        sizer = wx.BoxSizer(orient=wx.VERTICAL)
        hwin = LocalHtmlWindow(self, size=(600, 200))
        hwin.set_content(f"{SPC}New version {uversion} available from <a href=\"{url}\">{url}</a><br/>"
                         f"{SPC}See this version <a href=\"https://github.com/robotframework/RIDE/blob/master/doc"
                         f"/releasenotes/ride-{uversion}.rst\">Release Notes</a><br/><br/>"
                         f"{SPC}You can update with the command:<br/><b>{self._command}</b>"
                         f"<br/><br/>{SPC}Or, click <b>Upgrade Now</b>.<br/>"
                         f"{SPC}After upgrade you will see another dialog informing to close this RIDE instance.</b>"
                         f"<br/><br/>{SPC}See the latest development <a href=\"https://github.com/robotframework/RIDE"
                         f"/blob/master/CHANGELOG.adoc\">CHANGELOG</a>")
        irep = hwin.GetInternalRepresentation()
        hwin.SetSize((irep.GetWidth()+25, irep.GetHeight()+20))
        sizer.Add(hwin)
        checkbox = wx.CheckBox(self, -1, label="I\'m using another method for RIDE updates\n and "
                                               "do not need automatic update checks")
        checkbox.Bind(wx.EVT_CHECKBOX, handler=self.on_checkbox_change)
        sizer.Add(checkbox)
        hsizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        button = ButtonWithHandler(self, label="remind me later", handler=self.on_remind_me_later)
        button.SetBackgroundColour(Colour(self.color_secondary_background))
        button.SetForegroundColour(Colour(self.color_secondary_foreground))
        hsizer.Add(button)
        hsizer.AddSpacer(50)
        up_button = ButtonWithHandler(self, label="Upgrade Now", handler=self.on_upgrade_now)
        up_button.SetBackgroundColour(Colour(self.color_secondary_background))
        up_button.SetForegroundColour(Colour(self.color_secondary_foreground))
        hsizer.Add(up_button)
        sizer.Add(hsizer)
        self.SetSizer(sizer)
        self.CentreOnParent(wx.BOTH)
        self.Fit()
        self.SetFocus()
        if modal:
            self.ShowModal()
            self.Destroy()
        else:
            self.Show()

    def on_remind_me_later(self, event):
        _ = event
        self.Close(True)

    def on_checkbox_change(self, event):
        self._settings[_CHECK_FOR_UPDATES_SETTING] = not event.IsChecked()
        event.Skip()

    def on_upgrade_now(self, event):
        _ = event
        _add_content_to_clipboard(self._command)
        do_upgrade(self._command)
