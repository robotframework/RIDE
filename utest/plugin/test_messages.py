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
from nose.tools import assert_equal, assert_true, assert_raises
from robotide.publish import RideMessage, RideLog
from robotide.pluginapi import Plugin


class RideTestMessage(RideMessage):
    pass


class UnsubscribedRideTestMessage(RideMessage):
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
        assert_equal(self.plugin.class_handler_topic, RideTestMessage.topic())

    def test_subscribing_with_string(self):
        assert_raises(TypeError, self.plugin.subscribe, self.plugin.OnTestEventClass, 'ride.test')

    def test_event_with_data(self):
        RideMessageWithData(data_item='Data', more_data=[1, 2, 3]).publish()
        assert_equal(self.plugin.record['data_item'], 'Data')
        assert_equal(self.plugin.record['more_data'], [1, 2, 3])

    def test_subscribing_multiple_times(self):
        RideTestMessage().publish()
        assert_equal(self.plugin.count, 1)

    def test_subscribing_to_multiple_topics(self):
        RideMessageWithData(data_item='', more_data={}).publish()
        RideTestMessage().publish()
        assert_equal(self.plugin.multi_events,
                     ['ride.message.with.data', 'ride.test'])

    def test_subscribing_to_hierarchy(self):
        RideTestMessage().publish()
        RideMessageWithData(data_item=None, more_data=[]).publish()
        assert_equal(self.plugin.hierarchy_events,
                     ['ride.test', 'ride.message.with.data'])


class TestUnsubscribingFromEvents(unittest.TestCase):

    def setUp(self):
        self.plugin = SubscribingPlugin()
        self._unsubscribe_all = True

    def tearDown(self):
        if self._unsubscribe_all:
            self.plugin.unsubscribe_all()

    def test_unsubscribe_with_class(self):
        self.plugin.unsubscribe(self.plugin.OnTestEventClass, RideTestMessage)
        RideTestMessage().publish()
        assert_equal(self.plugin.class_handler_topic, None)

    def test_unsubscribe_with_string(self):
        assert_raises(TypeError, self.plugin.unsubscribe, self.plugin.OnTestEventClass, 'RideTestMessage')

    def test_unsubscribing_multiple_times_subscribed_once(self):
        self.plugin.unsubscribe(self.plugin.counting_handler, RideTestMessage)
        RideTestMessage().publish()
        assert_equal(self.plugin.count, 0)

    def test_unsubscribing_multiple_times_subscribed_all(self):
        for _ in range(5):
            self.plugin.unsubscribe(
                self.plugin.counting_handler, RideTestMessage)
        RideTestMessage().publish()
        assert_equal(self.plugin.count, 0)

    def test_unsubscribing_from_hierarchy(self):
        self.plugin.unsubscribe(self.plugin.hierarchical_listener, RideMessage)
        RideTestMessage().publish()
        RideMessageWithData(data_item='Data', more_data=[1, 2, 3]).publish()
        assert_equal(self.plugin.hierarchy_events, [])

    def test_unsubscribing_from_one_of_the_multiple_topics(self):
        self.plugin.unsubscribe(self.plugin.multiple_events_listening_handler,
                                RideMessageWithData)
        RideMessageWithData(data_item='data', more_data='').publish()
        RideTestMessage().publish()
        assert_equal(self.plugin.multi_events, ['ride.test'])

    def test_unsubscribing_from_not_subscribed_event_will_fail(self):
        assert_raises(Exception, self.plugin.unsubscribe, self.plugin.OnTestEventClass, UnsubscribedRideTestMessage)

    def test_unsubscribe_all(self):
        self.plugin.unsubscribe_all()
        self._unsubscribe_all = False
        RideTestMessage().publish()
        RideMessageWithData(data_item='Data', more_data=[1, 2, 3]).publish()
        assert_equal(self.plugin.class_handler_topic, None)
        assert_equal(self.plugin.record, {})
        assert_equal(self.plugin.count, 0)
        assert_equal(self.plugin.hierarchy_events, [])


class TestBrokenMessageListener(unittest.TestCase):

    def setUp(self):
        self.plugin = BrokenListenerPlugin()

    def tearDown(self):
        self.plugin.disable()

    def test_broken_listener(self):
        self.plugin.subscribe(self.plugin.error_listener, RideLog)
        RideTestMessage().publish()
        assert_true(self.plugin.error.message.startswith(
            'Error in listener: BrokenListenerPlugin.broken_listener'),
            'Wrong error message text: ' + self.plugin.error.message)
        assert_equal(self.plugin.error.topic(), 'ride.log.exception')
        assert_equal(self.plugin.error.level, 'ERROR')

    def test_broken_error_listener_does_not_cause_infinite_recusrion(self):
        self.plugin.subscribe(self.plugin.broken_listener, RideLog)


class BrokenListenerPlugin(Plugin):

    def __init__(self):
        self.subscribe(self.broken_listener, RideTestMessage)

    def disable(self):
        self.unsubscribe_all()

    def broken_listener(self, message):
        raise RuntimeError(message.topic())

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
        self.class_handler_topic = None

    def _subscribe_to_events(self):
        self.subscribe(self.OnTestEventClass, RideTestMessage)
        self.subscribe(self.OnTestEventWithData, RideMessageWithData)
        for _ in range(5):
            self.subscribe(self.counting_handler, RideTestMessage)
        self.subscribe(self.hierarchical_listener, RideMessage)
        self.subscribe(self.multiple_events_listening_handler, RideTestMessage,
                       RideMessageWithData)

    def OnTestEventClass(self, message):
        self.class_handler_topic = message.topic()

    def OnTestEventWithData(self, message):
        self.record['data_item'] = message.data_item
        self.record['more_data'] = message.more_data

    def counting_handler(self, message):
        self.count += 1

    def hierarchical_listener(self, message):
        self.hierarchy_events.append(message.topic())

    def multiple_events_listening_handler(self, message):
        self.multi_events.append(message.topic())


if __name__ == '__main__':
    unittest.main()
