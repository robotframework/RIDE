import unittest

from nose.tools import assert_equals, assert_raises, assert_true

from robotide.publish.messages import RideMessage, RideLogMessage, RideLogException
from robotide.publish.publisher import Publisher


class RideTestMessage(RideMessage):
    topic = 'My.Topic'


class RideTestMessageWithAttrs(RideTestMessage):
    data = ['foo', 'bar']


class RideTestMessageWithLongName(RideTestMessage):
    pass


class TestMessage(unittest.TestCase):

    def test_topic(self):
        assert_equals(RideMessage().topic, 'ride')
        assert_equals(RideTestMessage().topic, 'my.topic')
        assert_equals(RideTestMessageWithLongName().topic,
                      'ride.test.message.with.long.name')

    def test_all_attributes_given(self):
        msg = RideTestMessageWithAttrs(foo='bar', bar='quux')
        assert_equals(msg.foo, 'bar')
        assert_equals(msg.bar, 'quux')

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
        assert_equals(msg.message, 'Some error text')
        assert_equals(msg.level, 'ERROR')
        assert_true(msg.timestamp.startswith('20'))

    def test_log_exception(self):
        try:
            1 / 0
        except Exception, err:
            msg = RideLogException(
                message='Some error text', exception=err, level='ERROR')
            assert_true(msg.message.startswith(
                'Some error text\n\nTraceback (most recent call last):'))
            assert_equals(msg.level, 'ERROR')
            assert_true(msg.timestamp.startswith('20'))


class TestPublisher(unittest.TestCase):

    def setUp(self):
        self._msg = ''

    def test_publishing_string_message(self):
        pub = Publisher()
        pub.subscribe(self._listener, 'test.message')
        pub.publish('test.message', 'content')
        assert_equals(self._msg, 'content')

    def test_broken_string_message_listener(self):
        pub = Publisher()
        pub.subscribe(self._broken_listener, 'test.message')
        pub.publish('test.message', 'content')
        assert_equals(self._msg, 'content')

    def _listener(self, data):
        self._msg = data

    def _broken_listener(self, data):
        self._msg = data
        raise RuntimeError(data)
