import os
import unittest

from robot.utils.asserts import assert_equals

from robotide.event import RideEvent, publish
from robotide.plugins import Plugin
from robotide.plugins.loader import PluginLoader
from robotide.plugins.releasenotes import ReleaseNotesPlugin
ReleaseNotesPlugin.auto_show = lambda *args: None
from plugin_resources import FakeApplication, RideTestEvent, RideTestEventWithData


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
        self.record = {}
        self.count = 0
        self.events = []
        self.subscribe(self.OnTestEventClass, RideTestEvent)
        self.subscribe(self.OnTestEventString, 'ride.test')
        self.subscribe(self.OnTestEventStringWrongCase, 'RIDE.tesT')
        self.subscribe(self.OnTestEventWithData, RideTestEventWithData)
        for _ in range(5):
            self.subscribe(self.counting_handler, RideTestEvent)
        self.subscribe(self.hierarchical_listener, RideEvent)

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
        publish(RideTestEvent())
        assert_equals(self.plugin.class_handler_topic, 'Ride.Test')

    def test_subscribing_with_string(self):
        publish(RideTestEvent())
        assert_equals(self.plugin.string_handler_topic, 'Ride.Test')

    def test_subscribing_with_string_is_case_insensitive(self):
        publish(RideTestEvent())
        assert_equals(self.plugin.case_insensitive_string_handler_topic, 'Ride.Test')

    def test_event_with_data(self):
        publish(RideTestEventWithData(data_item='Data', more_data=[1,2,3]))
        assert_equals(self.plugin.record['data_item'], 'Data')
        assert_equals(self.plugin.record['more_data'], [1,2,3])

    def test_subscribing_multiple_times(self):
        publish(RideTestEvent())
        assert_equals(self.plugin.count, 5)

    def test_subscribing_to_hierarchy(self):
        publish(RideTestEvent())
        publish(RideTestEventWithData(data_item='Data', more_data=[1,2,3]))
        assert_equals(self.plugin.events, ['Ride.Test', 'Ride.Test.Event.With.Data'])

if __name__ == '__main__':
    unittest.main()
