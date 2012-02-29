import unittest
import time
from robotide.application.updatenotifier import UpdateNotifierController


class UpdateNotifierTestCase(unittest.TestCase):

    def test_normal_update(self):
        settings = {'check for updates':True,
                    'last update check':time.time()-60*60*24*7}
        ctrl = UpdateNotifierController(settings)
        self.assertTrue(ctrl.should_check())
        self.assertTrue(ctrl.is_new_version_available())
        version, url = ctrl.get_new_version_information()
        self.assertEqual('new version', version)
        self.assertEqual('download url', url)
        self.assertTrue(settings['check for updates'])
        self.assertTrue(settings['last update check'] > time.time() - 1)

    def test_last_update_done_less_than_a_week_ago(self):
        original_time = time.time()-60*60*24*3
        settings = {'check for updates':True,
                    'last update check':original_time}
        ctrl = UpdateNotifierController(settings)
        self.assertFalse(ctrl.should_check())
        self.assertTrue(settings['check for updates'])
        self.assertEqual(original_time, settings['last update check'])

    def test_check_for_updates_is_false(self):
        original_time = time.time()-60*60*24*7
        settings = {'check for updates':False,
                    'last update check':original_time}
        ctrl = UpdateNotifierController(settings)
        self.assertFalse(ctrl.should_check())
        self.assertFalse(settings['check for updates'])
        self.assertEqual(original_time, settings['last update check'])

    def test_no_update_found(self):
        pass

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
