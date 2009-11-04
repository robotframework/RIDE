import unittest
from robotide.event import RideEvent
from robot.utils.asserts import *


class TestEvent(unittest.TestCase):

    def test_topic(self):
        assert_equals(RideEvent().topic, 'Ride')
        assert_equals(RideTestEvent().topic, 'Ride.Test')
        assert_equals(RideTestNodeEvent().topic, 'Ride.Test.Node')

    def test_all_attributes_given(self):
        evt = RideTestEventWithAttrs(foo='bar', bar='quux')
        assert_equals(evt.foo, 'bar')
        assert_equals(evt.bar, 'quux')

    def test_missing_mandatory_attribute(self):
        msg = 'Missing mandatory attributes: bar'
        assert_raises_with_msg(AttributeError, msg, RideTestEventWithAttrs, 
                               foo='bar')

    def test_missing_many_mandatory_attributes(self):
        msg = 'Missing mandatory attributes: foo, bar'
        assert_raises_with_msg(AttributeError, msg, RideTestEventWithAttrs)

    def test_no_such_attribute_should_fail(self):
        msg = 'RideTestEventWithAttrs has no attribute quux'
        assert_raises_with_msg(AttributeError, msg, RideTestEventWithAttrs,
                               foo='', bar='', quux='camel')


class RideTestEvent(RideEvent):
    pass

class RideTestEventWithAttrs(RideTestEvent):
    _attrs = ['foo', 'bar']


class RideTestNodeEvent(RideTestEvent):
    pass


if __name__ == '__main__':
    unittest.main()