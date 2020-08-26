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

from nose.tools import assert_equal, assert_raises, assert_true

from robotide.publish.messages import (RideMessage, RideLogMessage,
                                       RideLogException)
from robotide.publish.publisher import PUBLISHER


class RideTestMessage(RideMessage):
    topic = 'My.Topic'


class RideTestMessageWithAttrs(RideTestMessage):
    data = ['foo', 'bar']


class RideTestMessageWithLongName(RideTestMessage):
    pass


class TestMessage(unittest.TestCase):

    def test_topic(self):
        assert_equal(RideMessage().topic, 'ride')
        assert_equal(RideTestMessage().topic, 'my.topic')
        assert_equal(RideTestMessageWithLongName().topic,
                     'ride.test.message.with.long.name')

    def test_all_attributes_given(self):
        msg = RideTestMessageWithAttrs(foo='bar', bar='quux')
        assert_equal(msg.foo, 'bar')
        assert_equal(msg.bar, 'quux')

    def test_missing_mandatory_attribute(self):
        assert_raises(TypeError, RideTestMessageWithAttrs, foo='bar')

    def test_missing_many_mandatory_attributes(self):
        assert_raises(TypeError, RideTestMessageWithAttrs)

    def test_no_such_attribute_should_fail(self):
        assert_raises(TypeError, RideTestMessageWithAttrs, foo='', bar='',
                      quux='camel')


class TestRideLogMessage(unittest.TestCase):

    def test_log_message(self):
        msg = RideLogMessage(message='Some error text', level='ERROR')
        assert_equal(msg.message, 'Some error text')
        assert_equal(msg.level, 'ERROR')
        assert_true(msg.timestamp.startswith('20'))

    def test_log_exception(self):
        try:
            1 / 0
        except Exception as err:
            msg = RideLogException(
                message='Some error text', exception=err, level='ERROR')
            assert_true(msg.message.startswith(
                'Some error text\n\nTraceback (most recent call last):'))
            assert_equal(msg.level, 'ERROR')
            assert_true(msg.timestamp.startswith('20'))


def _common_listener(message):
    TestPublisher.cls_msg = message
    TestPublisher.cls_msgs.append(message)


class DummyClass:

    def __init__(self):
        PUBLISHER.subscribe(self._dummy_listener, RideTestMessageWithAttrs)

    def _dummy_listener(self, message):
        TestPublisher.cls_msg = message
        TestPublisher.cls_msgs.append(message)


class TestPublisher(unittest.TestCase):
    cls_msg = ''
    cls_msgs = list()

    def setUp(self):
        self._msg = ''
        self.dummy_obj = None
        TestPublisher.cls_msg = ''
        TestPublisher.cls_msgs.clear()

    def tearDown(self):
        PUBLISHER.unsubscribe_all(self)

    def test_publishing_string_message(self):
        PUBLISHER.subscribe(self._listener, 'test.message1')
        PUBLISHER.publish('test.message1', 'content')
        assert_equal(self._msg, 'content')

    def test_publishing_ride_message(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.publish(RideTestMessageWithAttrs, 'content3')
        assert_equal(self._msg, 'content3')

    def test_publishing_ride_message2(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(self._msg, msg_obj)

    def test_publishing_common_listener(self):
        PUBLISHER.subscribe(_common_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        PUBLISHER.unsubscribe(_common_listener, RideTestMessageWithAttrs)
        assert_equal(TestPublisher.cls_msg, msg_obj)

    def test_unsubscribe_ride_message(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.unsubscribe(self._listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(self._msg, '')

    def test_subscribe_multi_listeners(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._broken_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 4)

    def test_subscribe_multi_listeners2(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._broken_listener, RideTestMessage)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 3 * 2)

    def test_unsubscribe_all(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._broken_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 4)
        PUBLISHER.unsubscribe_all(self)
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 4)

    def test_unsubscribe_all2(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._broken_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        self.dummy_obj = DummyClass()
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 5)
        PUBLISHER.unsubscribe_all(self)
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 6)

    def test_unsubscribe_all3(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._broken_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        self.dummy_obj = DummyClass()
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 5)
        PUBLISHER.unsubscribe_all(self.dummy_obj)
        PUBLISHER.unsubscribe_all(self)
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 5)

    def test_subscribe_obj_weak_ref(self):
        self.dummy_obj = DummyClass()
        del self.dummy_obj
        assert_equal(hasattr(self, 'dummy_obj'), False)

    def test_unsubscribe_string_message(self):
        PUBLISHER.subscribe(self._listener, 'RideTestMessageWithAttrs')
        PUBLISHER.unsubscribe(self._listener, 'RideTestMessageWithAttrs')
        PUBLISHER.publish('RideTestMessageWithAttrs', 'test')
        assert_equal(self._msg, '')

    def test_subscribe_static_method(self):
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(TestPublisher.cls_msg, msg_obj)

    def test_subscribe_class_method(self):
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(TestPublisher.cls_msg, msg_obj)

    def test_broken_string_message_listener(self):
        PUBLISHER.subscribe(self._broken_listener, 'test.message2')
        PUBLISHER.publish('test.message2', 'content2')
        assert_equal(self._msg, 'content2')

    def _listener(self, message):
        self._msg = message
        TestPublisher.cls_msgs.append(message)

    def _broken_listener(self, message):
        self._msg = message
        TestPublisher.cls_msgs.append(message)
        raise RuntimeError(message)

    @staticmethod
    def _static_listener(message):
        TestPublisher.cls_msg = message
        TestPublisher.cls_msgs.append(message)

    @classmethod
    def _class_listener(cls, message):
        cls.cls_msg = message
        TestPublisher.cls_msgs.append(message)


if __name__ == '__main__':
    unittest.main()
