import unittest

from nose.tools import assert_equals, assert_false, assert_true

from robotide.publish import RideMessage, RideLog, PUBLISHER
from robotide.pluginapi import Plugin


class RideTestMessage(RideMessage):
    pass


class RideMessageWithData(RideMessage):
    data = ['data_item', 'more_data']


class TestSubscribingToEvents(unittest.TestCase):

    def setUp(self):
        self.plugin = SubscribingPlugin()

    def tearDown(self):
        self.plugin.disable()

    def test_subscribing_with_class(self):
        RideTestMessage().publish()
        assert_equals(self.plugin.class_handler_topic, 'ride.test')

    def test_subscribing_with_string(self):
        RideTestMessage().publish()
        assert_equals(self.plugin.string_handler_topic, 'ride.test')

    def test_subscribing_with_string_is_case_insensitive(self):
        RideTestMessage().publish()
        assert_equals(self.plugin.case_insensitive_string_handler_topic,
                      'ride.test')

    def test_event_with_data(self):
        RideMessageWithData(data_item='Data', more_data=[1, 2, 3]).publish()
        assert_equals(self.plugin.record['data_item'], 'Data')
        assert_equals(self.plugin.record['more_data'], [1, 2, 3])

    def test_subscribing_multiple_times(self):
        RideTestMessage().publish()
        assert_equals(self.plugin.count, 5)

    def test_subscribing_to_multiple_topics(self):
        RideMessageWithData(data_item='', more_data={}).publish()
        RideTestMessage().publish()
        assert_equals(self.plugin.multi_events,
                      ['ride.message.with.data', 'ride.test'])

    def test_subscribing_to_hierarchy(self):
        RideTestMessage().publish()
        RideMessageWithData(data_item=None, more_data=[]).publish()
        assert_equals(self.plugin.hierarchy_events,
                      ['ride.test', 'ride.message.with.data'])


class TestUnsubscribingFromEvents(unittest.TestCase):

    def setUp(self):
        self.plugin = SubscribingPlugin()
        self._unsubscribe_all = True

    def tearDown(self):
        if self._unsubscribe_all:
            self.plugin.unsubscribe_all()

    def test_unsubscribe_with_class(self):
        listener_count = len(PUBLISHER._listeners[self.plugin])
        self.plugin.unsubscribe(self.plugin.OnTestEventClass, RideTestMessage)
        RideTestMessage().publish()
        assert_equals(self.plugin.class_handler_topic, None)
        assert_equals(
            len(PUBLISHER._listeners[self.plugin]), listener_count - 1)

    def test_unsubscribe_with_string(self):
        self.plugin.unsubscribe(self.plugin.OnTestEventString, 'ride.test')
        RideTestMessage().publish()
        assert_equals(self.plugin.string_handler_topic, None)

    def test_unsubscribe_with_string_is_case_insensitive(self):
        self.plugin.unsubscribe(
            self.plugin.OnTestEventStringWrongCase, 'RiDe.TEst')
        RideTestMessage().publish()
        assert_equals(self.plugin.case_insensitive_string_handler_topic, None)

    def test_unsubscribing_multiple_times_subscribed_once(self):
        self.plugin.unsubscribe(self.plugin.counting_handler, RideTestMessage)
        RideTestMessage().publish()
        assert_equals(self.plugin.count, 4)

    def test_unsubscribing_multiple_times_subscribed_all(self):
        for _ in range(5):
            self.plugin.unsubscribe(
                self.plugin.counting_handler, RideTestMessage)
        RideTestMessage().publish()
        assert_equals(self.plugin.count, 0)

    def test_unsubscribing_from_hierarchy(self):
        self.plugin.unsubscribe(self.plugin.hierarchical_listener, RideMessage)
        RideTestMessage().publish()
        RideMessageWithData(data_item='Data', more_data=[1, 2, 3]).publish()
        assert_equals(self.plugin.hierarchy_events, [])

    def test_unsubscribing_from_one_of_the_multiple_topics(self):
        self.plugin.unsubscribe(self.plugin.multiple_events_listening_handler,
                                RideMessageWithData)
        RideMessageWithData(data_item='data', more_data='').publish()
        RideTestMessage().publish()
        assert_equals(self.plugin.multi_events, ['ride.test'])

    def test_unsubscribing_from_multiple_topics(self):
        self.plugin.unsubscribe(self.plugin.multiple_events_listening_handler,
                                'Ride.test', RideMessageWithData)
        RideTestMessage().publish()
        RideMessageWithData(data_item='data', more_data='').publish()
        assert_equals(self.plugin.multi_events, [])

    def test_unsubscribing_from_not_subscribed_event_does_not_fail(self):
        self.plugin.unsubscribe(self.plugin.OnTestEventClass, 'Non.existing')

    def test_unsubscribe_all(self):
        self.plugin.unsubscribe_all()
        self._unsubscribe_all = False
        RideTestMessage().publish()
        RideMessageWithData(data_item='Data', more_data=[1, 2, 3]).publish()
        assert_equals(self.plugin.class_handler_topic, None)
        assert_equals(self.plugin.string_handler_topic, None)
        assert_equals(self.plugin.case_insensitive_string_handler_topic, None)
        assert_equals(self.plugin.record, {})
        assert_equals(self.plugin.count, 0)
        assert_equals(self.plugin.hierarchy_events, [])
        assert_false(self.plugin in PUBLISHER._listeners)


class TestBrokenMessageListener(unittest.TestCase):

    def setUp(self):
        self.plugin = BrokenListenerPlugin()

    def tearDown(self):
        self.plugin.disable()

    def test_broken_listener(self):
        self.plugin.subscribe(self.plugin.error_listener, RideLog)
        RideTestMessage().publish()
        assert_true(self.plugin.error.message.startswith(
            'Error in listener: ride.test'),
            'Wrong error message text: ' + self.plugin.error.message)
        assert_equals(self.plugin.error.topic, 'ride.log.exception')
        assert_equals(self.plugin.error.level, 'ERROR')

    def test_broken_error_listener_does_not_cause_infinite_recusrion(self):
        self.plugin.subscribe(self.plugin.broken_listener, RideLog)


class BrokenListenerPlugin(Plugin):

    def __init__(self):
        self.subscribe(self.broken_listener, RideTestMessage)

    def disable(self):
        self.unsubscribe_all()

    def broken_listener(self, message):
        raise RuntimeError(message.topic)

    def error_listener(self, message):
        self.error = message


class SubscribingPlugin(Plugin):

    def __init__(self):
        self._reset_recorders()
        self._subscribe_to_events()

    def disable(self):
        self.unsubscribe_all()

    def _reset_recorders(self):
        self.record = {}
        self.count = 0
        self.hierarchy_events = []
        self.multi_events = []
        self.class_handler_topic = self.string_handler_topic =\
            self.case_insensitive_string_handler_topic = None

    def _subscribe_to_events(self):
        self.subscribe(self.OnTestEventClass, RideTestMessage)
        self.subscribe(self.OnTestEventString, 'ride.test')
        self.subscribe(self.OnTestEventStringWrongCase, 'RIDE.tesT')
        self.subscribe(self.OnTestEventWithData, RideMessageWithData)
        for _ in range(5):
            self.subscribe(self.counting_handler, RideTestMessage)
        self.subscribe(self.hierarchical_listener, RideMessage)
        self.subscribe(self.multiple_events_listening_handler, RideTestMessage,
                       RideMessageWithData)

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
        self.hierarchy_events.append(event.topic)

    def multiple_events_listening_handler(self, event):
        self.multi_events.append(event.topic)


if __name__ == '__main__':
    unittest.main()
