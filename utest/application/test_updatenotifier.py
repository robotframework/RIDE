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

import unittest
import time
import urllib as urllib2

from robotide.application.updatenotifier import UpdateNotifierController


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

    def _update_notifier_controller(self, settings, current, new, url='some url'):
        ctrl = UpdateNotifierController(settings)
        ctrl.VERSION = current
        ctrl._get_newest_version = lambda: new
        ctrl._get_download_url = lambda v: url if v == new else None
        return ctrl

    def _settings(self, check_for_updates=True, last_update_check=time.time() - 60 * 60 * 24 * 7 - 1):
        return {'check for updates': check_for_updates,
                'last update check': last_update_check}

    def test_normal_update(self):
        settings = self._settings()
        ctrl = self._update_notifier_controller(settings, '0', '1', 'http://xyz.abc.efg.di')
        ctrl.notify_update_if_needed(self._callback)
        self.assertEqual('1', self._version)
        self.assertEqual('http://xyz.abc.efg.di', self._url)
        self.assertTrue(self._callback_called)
        self.assertTrue(settings['check for updates'])
        self.assertTrue(settings['last update check'] > time.time() - 1)

    def test_update_when_trunk_version(self):
        settings = self._settings()
        ctrl = self._update_notifier_controller(settings, 'trunk', '0.56')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(self._callback_called)
        self.assertEqual('0.56', self._version)
        self.assertTrue(settings['check for updates'])
        self.assertTrue(settings['last update check'] > time.time() - 1)

    def test_last_update_done_less_than_a_week_ago(self):
        original_time = time.time() - 60 * 60 * 24 * 3
        settings = self._settings(last_update_check=original_time)
        ctrl = UpdateNotifierController(settings)
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings['check for updates'])
        self.assertEqual(original_time, settings['last update check'])
        self.assertFalse(self._callback_called)

    def test_check_for_updates_is_false(self):
        settings = self._settings(check_for_updates=False)
        original_time = settings['last update check']
        ctrl = UpdateNotifierController(settings)
        ctrl.notify_update_if_needed(self._callback)
        self.assertFalse(settings['check for updates'])
        self.assertEqual(original_time, settings['last update check'])
        self.assertFalse(self._callback_called)

    def test_no_update_found(self):
        settings = self._settings()
        ctrl = self._update_notifier_controller(settings, '0.55', '0.55')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings['last update check'] > time.time() - 1)
        self.assertFalse(self._callback_called)

    def test_first_run_sets_settings_correctly_and_checks_for_updates(self):
        settings = self._settings(check_for_updates=None, last_update_check=None)
        ctrl = self._update_notifier_controller(settings, '1.0.2', '1.0.2')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings['last update check'] > time.time() - 1)
        self.assertTrue(settings['check for updates'])
        self.assertFalse(self._callback_called)

    def test_first_run_sets_settings_correctly_and_finds_an_update(self):
        settings = self._settings(check_for_updates=None, last_update_check=None)
        ctrl = self._update_notifier_controller(settings, '1.2', '2.0')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings['last update check'] > time.time() - 1)
        self.assertTrue(settings['check for updates'])
        self.assertTrue(self._callback_called)

    def test_checking_timeouts(self):
        settings = self._settings()
        ctrl = UpdateNotifierController(settings)

        def throwTimeoutError():
            raise urllib2.URLError('timeout')

        ctrl._get_newest_version = throwTimeoutError
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings['last update check'] > time.time() - 1)
        self.assertFalse(self._callback_called)

    def test_download_url_checking_timeouts(self):
        settings = self._settings()
        ctrl = UpdateNotifierController(settings)
        ctrl.VERSION = '0'
        ctrl._get_newest_version = lambda: '1'

        def throwTimeoutError(*args):
            raise urllib2.URLError('timeout')

        ctrl._get_download_url = throwTimeoutError
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings['last update check'] > time.time() - 1)
        self.assertFalse(self._callback_called)

    def test_server_returns_no_versions(self):
        settings = self._settings()
        ctrl = self._update_notifier_controller(settings, '1.2.2', None)
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings['last update check'] > time.time() - 1)
        self.assertTrue(settings['check for updates'])
        self.assertFalse(self._callback_called)

    def test_server_returns_older_version(self):
        settings = self._settings()
        ctrl = self._update_notifier_controller(settings, '0.44', '0.43.1')
        ctrl.notify_update_if_needed(self._callback)
        self.assertTrue(settings['last update check'] > time.time() - 1)
        self.assertTrue(settings['check for updates'])
        self.assertFalse(self._callback_called)


if __name__ == '__main__':
    unittest.main()
