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

# Configure wx version to allow running test app in __main__


import time
import urllib.request as urllib2
import xmlrpc.client as xmlrpclib

import wx
from wx import Colour

from .. import version
from ..utils.versioncomparator import cmp_versions
from ..widgets import ButtonWithHandler, HtmlWindow, RIDEDialog

_CHECK_FOR_UPDATES_SETTING = "check for updates"
_LAST_UPDATE_CHECK_SETTING = "last update check"


class UpdateNotifierController(object):

    VERSION = version.VERSION
    SECONDS_IN_WEEK = 60*60*24*7

    def __init__(self, settings):
        self._settings = settings

    def notify_update_if_needed(self, update_notification_callback):
        if self._should_check() and self._is_new_version_available():
            update_notification_callback(self._newest_version, self._download_url, self._settings)

    def _should_check(self):
        if self._settings.get(_CHECK_FOR_UPDATES_SETTING, None) is None:
            self._settings[_CHECK_FOR_UPDATES_SETTING] = True
            return True
        return self._settings[_CHECK_FOR_UPDATES_SETTING] and \
               time.time() - self._settings.get(_LAST_UPDATE_CHECK_SETTING, 0) > self.SECONDS_IN_WEEK

    def _is_new_version_available(self):
        self._settings[_LAST_UPDATE_CHECK_SETTING] = time.time()
        try:
            self._newest_version = self._get_newest_version()
            self._download_url = self._get_download_url(self._newest_version)
        except Exception as e:
            print(e)
            #There are many possible errors:
            # - Timeout
            # - Corrupted data
            # - Server fault message
            # - Unexpected change in dataformat
            return False
        return cmp_versions(self.VERSION, self._newest_version) == -1

    def _get_newest_version(self):
        return self._get_response(('robotframework-ride',), 'package_releases')[0]

    def _get_download_url(self, version):
        from time import sleep
        sleep(1)  # To avoid HTTPTooManyRequests
        return self._get_response(('robotframework-ride', version), 'release_data')['download_url']

    def _get_response(self, params, method):
        xmlparm = xmlrpclib.dumps(params, method)
        req = urllib2.Request('https://pypi.python.org/pypi',
                              xmlparm.encode('utf-8'),
                              {'Content-Type':'text/xml'})
        data = urllib2.urlopen(req, timeout=1).read()
        xml = xmlrpclib.loads(data)[0][0]
        return xml


class LocalHtmlWindow(HtmlWindow):
    def __init__(self, parent, size=(600,400)):
        HtmlWindow.__init__(self, parent, size)
        if "gtk2" or "gtk3" in wx.PlatformInfo:
            self.SetStandardFonts()

    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())


class UpdateDialog(RIDEDialog):

    def __init__(self, version, url, settings):
        self._settings = settings
        RIDEDialog.__init__(self, title="Update available", size=(400, 400),
                            style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        sizer = wx.BoxSizer(orient=wx.VERTICAL)
        hwin = LocalHtmlWindow(self, size=(400, 200))
        hwin.set_content(f"New version {version} available from <a href=\"{url}\">{url}</a><br/>"
                         f"See this version <a href=\"https://github.com/robotframework/RIDE/blob/master/doc"
                         f"/releasenotes/ride-{version}.rst\">Release Notes</a><br/><br/>"
                         f"You can update with the command:<br/><b>pip install -U robotframework-ride</b>"
                         f"<br/><br/>See the latest development <a href=\"https://github.com/robotframework/RIDE"
                         f"/blob/master/CHANGELOG.adoc\">CHANGELOG</a>")
        irep = hwin.GetInternalRepresentation()
        hwin.SetSize((irep.GetWidth()+25, irep.GetHeight()+20))
        sizer.Add(hwin)
        checkbox = wx.CheckBox(self, -1, label="I\'m using another method for RIDE updates\n and "
                                               "do not need automatic update checks")
        checkbox.Bind(wx.EVT_CHECKBOX, handler=self.OnCheckboxChange)
        sizer.Add(checkbox)
        button = ButtonWithHandler(self, label="remind me later", handler=self.OnRemindMeLater)
        button.SetBackgroundColour(Colour(self.color_secondary_background))
        button.SetForegroundColour(Colour(self.color_secondary_foreground))
        sizer.Add(button)
        self.SetSizer(sizer)
        self.CentreOnParent(wx.BOTH)
        self.Fit()
        self.SetFocus()
        self.ShowModal()
        self.Destroy()

    def OnRemindMeLater(self, event):
        self.Close(True)

    def OnCheckboxChange(self, event):
        self._settings[_CHECK_FOR_UPDATES_SETTING] = not event.IsChecked()
        event.Skip()
