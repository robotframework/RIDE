import unittest

from robot.utils.asserts import assert_equals, assert_raises_with_msg

from robotide.event import RideEvent


_ARGS_ERROR = "Argument mismatch, expected: ['foo', 'bar']"


class RideTestEvent(RideEvent):
    topic = 'My.Topic'

class RideTestEventWithAttrs(RideTestEvent):
    attr_names = ['foo', 'bar']

class RideTestEventWithLongName(RideTestEvent):
    pass


class TestEvent(unittest.TestCase):

    def test_topic(self):
        assert_equals(RideEvent().topic, 'Ride')
        assert_equals(RideTestEvent().topic, 'My.Topic')
        assert_equals(RideTestEventWithLongName().topic,
                      'Ride.Test.Event.With.Long.Name')

    def test_all_attributes_given(self):
        evt = RideTestEventWithAttrs(foo='bar', bar='quux')
        assert_equals(evt.foo, 'bar')
        assert_equals(evt.bar, 'quux')

    def test_missing_mandatory_attribute(self):
        assert_raises_with_msg(TypeError, _ARGS_ERROR,
                               RideTestEventWithAttrs, foo='bar')

    def test_missing_many_mandatory_attributes(self):
        assert_raises_with_msg(TypeError, _ARGS_ERROR, RideTestEventWithAttrs)

    def test_no_such_attribute_should_fail(self):
        assert_raises_with_msg(TypeError, _ARGS_ERROR, RideTestEventWithAttrs,
                               foo='', bar='', quux='camel')


if __name__ == '__main__':
    unittest.main()
