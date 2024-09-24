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
import typing
import unittest
import time
import urllib

import pytest
import wx

from robotide.application.updatenotifier import UpdateNotifierController, UpdateDialog

CHECKFORUPDATES = 'check for updates'
LASTUPDATECHECK = 'last update check'


class UpdateNotifierTestCase(unittest.TestCase):

    def setUp(self):
        self._callback_called = False
        self._version = None
        self._url = None

    def _callback(self, version, url, settings):
        self.assertFalse(self._callback_called)
        self._callback_called = True
        self.assertNotEqual(None, version)
        self._version = version
        self.assertNotEqual(None, url)
        self._url = url
        self.assertEqual(dict, type(settings))

    @staticmethod
    def _update_notifier_controller(settings, current, new, url='some url'):
        ctrl = UpdateNotifierController(settings)
        ctrl.VERSION = current
        ctrl._get_newest_version = lambda: new
        ctrl._get_download_url = lambda v: url if v == new else None
        return ctrl

    @staticmethod
    def internal_settings(check_for_updates: typing.Union[bool, None] = True,
                          last_update_check: typing.Union[float, None] = time.time() - 60 * 60 * 24 * 7 - 1):
        return {CHECKFORUPDATES: check_for_updates,
                LASTUPDATECHECK: last_update_check}

    def test_normal_update(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, '0', '1', 'http://xyz.abc.efg.di')
        ctrl.notify_update_if_needed(self._callback)
        self.assertEqual('1', self._version)
        self.assertEqual('http://xyz.abc.efg.di', self._url)
        self.assertTrue(self._callback_called)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 1)

    def test_update_when_trunk_version(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, '2.0', '2.0.1')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(self._callback_called)
        self.assertEqual('2.0.1', self._version)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 1)

    def test_last_update_done_less_than_a_week_ago(self):
        original_time = time.time() - 60 * 60 * 24 * 3
        settings = self.internal_settings(last_update_check=original_time)
        ctrl = UpdateNotifierController(settings)
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertEqual(original_time, settings[LASTUPDATECHECK])
        self.assertFalse(self._callback_called)

    def test_check_for_updates_is_false(self):
        settings = self.internal_settings(check_for_updates=False)
        original_time = settings[LASTUPDATECHECK]
        ctrl = UpdateNotifierController(settings)
        ctrl.notify_update_if_needed(self._callback)
        self.assertFalse(settings[CHECKFORUPDATES])
        self.assertEqual(original_time, settings[LASTUPDATECHECK])
        self.assertFalse(self._callback_called)

    def test_no_update_found(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, '0.55', '0.55')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 1)
        self.assertFalse(self._callback_called)

    def test_no_update_found_dev(self):
        app = wx.App()
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, '0.56', '0.56')
        ctrl.notify_update_if_needed(self._callback, ignore_check_condition=False, show_no_update=False)
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 1)
        self.assertFalse(self._callback_called)

    def test_no_update_found_dev_notify(self):
        app = wx.App()
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, '0.55', '0.55')
        ctrl.notify_update_if_needed(self._callback, ignore_check_condition=True, show_no_update=True)
        self.assertFalse(self._callback_called)

    def test_first_run_sets_settings_correctly_and_checks_for_updates(self):
        settings = self.internal_settings(check_for_updates=None, last_update_check=None)
        ctrl = self._update_notifier_controller(settings, '1.0.2', '1.0.2')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 1)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertFalse(self._callback_called)

    def test_first_run_sets_settings_correctly_and_finds_an_update(self):
        settings = self.internal_settings(check_for_updates=None, last_update_check=None)
        ctrl = self._update_notifier_controller(settings, '1.2', '2.0')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 1)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertTrue(self._callback_called)

    def test_checking_timeouts(self):
        app = wx.App()
        settings = self.internal_settings()
        ctrl = UpdateNotifierController(settings)

        def throw_timeout_error():
            raise urllib.error.URLError('timeout')

        ctrl._get_newest_version = throw_timeout_error
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 10)  # The dialog timeout in 10 seconds
        self.assertFalse(self._callback_called)

    def test_download_url_checking_timeouts(self):
        settings = self.internal_settings()
        ctrl = UpdateNotifierController(settings)
        ctrl.VERSION = '0'
        ctrl._get_newest_version = lambda: '1'

        def throw_timeout_error(*args):
            _ = args
            raise urllib.error.URLError('timeout')

        ctrl._get_download_url = throw_timeout_error
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 1)
        self.assertFalse(self._callback_called)

    def test_server_returns_no_versions(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, '1.2.2', None)
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 1)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertFalse(self._callback_called)

    def test_server_returns_older_version(self):
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, '0.44', '0.43.1')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 1)
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertFalse(self._callback_called)

    def test_forced_check_released(self):
        app = wx.App()
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, '0.43.0', '0.43.1')
        ctrl.notify_update_if_needed(self._callback, ignore_check_condition=True)
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 19)  # The dialog timeout in 20 seconds
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertTrue(self._callback_called)

    def test_forced_check_development(self):
        app = wx.App()
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, '0.44dev12', '0.44.dev14')
        ctrl.notify_update_if_needed(self._callback, ignore_check_condition=True)
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 20)  # The dialog timeout in 20 seconds
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertTrue(self._callback_called)

    def test_forced_check_development_ok(self):
        app = wx.App()
        settings = self.internal_settings()
        ctrl = self._update_notifier_controller(settings, '0.44dev12', '0.44.dev12')
        ctrl.notify_update_if_needed(self._callback, ignore_check_condition=False)
        self.assertTrue(settings[LASTUPDATECHECK] > time.time() - 20)  # The dialog timeout in 20 seconds
        self.assertTrue(settings[CHECKFORUPDATES])
        self.assertFalse(self._callback_called)

    def test_normal_update_dialog(self):
        """ This is not actually doing a test """
        app = wx.App()
        frame = wx.Frame()
        notebook = wx.Notebook(frame)
        settings = self.internal_settings()
        ctrl=UpdateDialog('1.0.0', 'http://localhost', settings, notebook,False)
        wx.CallLater(3000, ctrl.EndModal,wx.CANCEL)
        ctrl.ShowModal()
        ctrl.Destroy()


if __name__ == '__main__':
    unittest.main()
