import unittest
import time
from robotide.application.updatenotifier import UpdateNotifierController


class UpdateNotifierTestCase(unittest.TestCase):

    def test_normal_update(self):
        settings = self._settings()
        ctrl = self._update_notifier_controller(settings, '0', '1')
        self.assertTrue(ctrl.should_check())
        self.assertTrue(ctrl.is_new_version_available())
        version, url = ctrl.get_new_version_information()
        self.assertEqual('1', version)
        self.assertEqual('download url', url)
        self.assertTrue(settings['check for updates'])
        self.assertTrue(settings['last update check'] > time.time() - 1)

    def _update_notifier_controller(self, settings, current, new):
        ctrl = UpdateNotifierController(settings)
        ctrl.VERSION = current
        ctrl._get_newest_version = lambda: new
        return ctrl

    def _settings(self, check_for_updates=True, last_update_check=None):
        return {'check for updates': check_for_updates,
                'last update check': last_update_check or time.time()-60*60*24*7}

    def test_last_update_done_less_than_a_week_ago(self):
        original_time = time.time()-60*60*24*3
        settings = self._settings(last_update_check=original_time)
        ctrl = UpdateNotifierController(settings)
        self.assertFalse(ctrl.should_check())
        self.assertTrue(settings['check for updates'])
        self.assertEqual(original_time, settings['last update check'])

    def test_check_for_updates_is_false(self):
        settings = self._settings(check_for_updates=False)
        original_time = settings['last update check']
        ctrl = UpdateNotifierController(settings)
        self.assertFalse(ctrl.should_check())
        self.assertFalse(settings['check for updates'])
        self.assertEqual(original_time, settings['last update check'])

    def test_no_update_found(self):
        settings = self._settings()
        ctrl = self._update_notifier_controller(settings, '0.55', '0.55')
        self.assertFalse(ctrl.is_new_version_available())
        self.assertTrue(settings['last update check'] > time.time() - 1)

    def test_first_run_sets_settings_correctly_and_checks_for_updates(self):
        pass

    def test_checking_timeouts(self):
        pass

    def test_server_returns_no_versions(self):
        pass

    def test_server_returns_older_version(self):
        pass

if __name__ == '__main__':
    unittest.main()
