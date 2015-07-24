import sys

from robotide.namespace import namespace, robotlibraryloader
from nose.tools import assert_true, assert_false
from mock import patch

from resources.mocks import FakeSettings


def test_bundled_libraries_path_is_in_sys_path_by_default():
    assert_true(namespace.BUNDLED_LIBRARIES_PATH in sys.path)


@patch.object(robotlibraryloader, 'find_installed_robot_libraries')
def test_bundle_path_is_removed_when_using_installed_rf_libraries(mock_func):
    namespace.Namespace(FakeSettings({'use installed robot libraries': True}))
    mock_func.assert_called_once_with(None)
    assert_true(namespace.REMOTE_LIB_PATH in sys.path)
    assert_false(namespace.BUNDLED_LIBRARIES_PATH in sys.path)
