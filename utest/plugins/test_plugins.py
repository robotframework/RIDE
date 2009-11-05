import os
import unittest

from robot.utils.asserts import assert_equals, assert_none

from robotide.event import RideEvent
from robotide.plugins import Plugin
from robotide.plugins.loader import PluginLoader
from robotide.plugins.releasenotes import ReleaseNotesPlugin
ReleaseNotesPlugin.auto_show = lambda *args: None
from plugin_resources import FakeApplication, RideTestEvent,\
    RideTestEventWithData


class TestablePluginLoader(PluginLoader):
    def _get_plugin_dirs(self):
        return [os.path.join(os.path.dirname(__file__), 'plugins_for_loader')]

class TestPluginLoader(unittest.TestCase):

    def test_plugin_loading(self):
        loader = TestablePluginLoader(FakeApplication())
        self._assert_plugin_loaded(loader, 'Example Plugin 1')
        self._assert_plugin_loaded(loader, 'Example Plugin 2')
        self._assert_plugin_loaded(loader, 'Example Plugin 3')
        self._assert_plugin_loaded(loader, 'Release Notes')

    def _assert_plugin_loaded(self, loader, name):
        for p in loader.plugins:
            if p.name == name:
                return
        raise AssertionError("Plugin '%s' not loaded" % name)


class SubscribingPlugin(Plugin):

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._reset_recorders()
        self._subscribe_or_unsubscribe_all(self.subscribe)

    def _reset_recorders(self):
        self.record = {}
        self.count = 0
        self.events = []
        self.class_handler_topic = self.string_handler_topic =\
            self.case_insensitive_string_handler_topic = None

    def _subscribe_or_unsubscribe_all(self, action):
        action(self.OnTestEventClass, RideTestEvent)
        action(self.OnTestEventString, 'ride.test')
        action(self.OnTestEventStringWrongCase, 'RIDE.tesT')
        action(self.OnTestEventWithData, RideTestEventWithData)
        for _ in range(5):
            action(self.counting_handler, RideTestEvent)
        action(self.hierarchical_listener, RideEvent)

    def unsubscribe_all(self):
        self._subscribe_or_unsubscribe_all(self.unsubscribe)
        self._reset_recorders()

    def OnTestEventClass(self, event):
        self.class_handler_topic = event.topic

    def OnTestEventString(self, event):
        self.string_handler_topic = event.topic

    def OnTestEventStringWrongCase(self, event):
        self.case_insensitive_string_handler_topic = event.topic

    def OnTestEventWithData(self, event):
        self.record['data_item'] = event.data_item
        self.record['more_data'] = event.more_data

    def counting_handler(self, event):
        self.count += 1

    def hierarchical_listener(self, event):
        self.events.append(event.topic)


class TestPluginEvents(unittest.TestCase):

    def setUp(self):
        self.plugin = SubscribingPlugin(FakeApplication())

    def test_subscribing_with_class(self):
        RideTestEvent().publish()
        assert_equals(self.plugin.class_handler_topic, 'Ride.Test')

    def test_subscribing_with_string(self):
        RideTestEvent().publish()
        assert_equals(self.plugin.string_handler_topic, 'Ride.Test')

    def test_subscribing_with_string_is_case_insensitive(self):
        RideTestEvent().publish()
        assert_equals(self.plugin.case_insensitive_string_handler_topic, 'Ride.Test')

    def test_event_with_data(self):
        RideTestEventWithData(data_item='Data', more_data=[1,2,3]).publish()
        assert_equals(self.plugin.record['data_item'], 'Data')
        assert_equals(self.plugin.record['more_data'], [1,2,3])

    def test_subscribing_multiple_times(self):
        RideTestEvent().publish()
        assert_equals(self.plugin.count, 5)

    def test_subscribing_to_hierarchy(self):
        RideTestEvent().publish()
        RideTestEventWithData(data_item='Data', more_data=[1,2,3]).publish()
        assert_equals(self.plugin.events, ['Ride.Test', 'Ride.Test.Event.With.Data'])

    def test_unsubscribe(self):
        self.plugin.unsubscribe_all()
        RideTestEvent().publish()
        RideTestEventWithData(data_item='Data', more_data=[1,2,3]).publish()
        assert_none(self.plugin.class_handler_topic)
        assert_none(self.plugin.string_handler_topic)
        assert_none(self.plugin.case_insensitive_string_handler_topic)
        assert_equals(self.plugin.record, {})
        assert_equals(self.plugin.count, 0)
        assert_equals(self.plugin.events, [])


if __name__ == '__main__':
    unittest.main()

