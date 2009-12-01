#  Copyright 2008 Nokia Siemens Networks Oyj
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

from robot.utils.asserts import assert_equals, assert_raises_with_msg,\
    assert_true

from robotide.publish import RideMessage, RideLogMessage


_ARGS_ERROR = "Argument mismatch, expected: ['foo', 'bar']"


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
        assert_raises_with_msg(TypeError, _ARGS_ERROR,
                               RideTestMessageWithAttrs, foo='bar')

    def test_missing_many_mandatory_attributes(self):
        assert_raises_with_msg(TypeError, _ARGS_ERROR, RideTestMessageWithAttrs)

    def test_no_such_attribute_should_fail(self):
        assert_raises_with_msg(TypeError, _ARGS_ERROR, RideTestMessageWithAttrs,
                               foo='', bar='', quux='camel')


class TestRideLogMessage(unittest.TestCase):

    def test_log_message(self):
        msg = RideLogMessage(message='Some error text', level='ERROR')
        assert_equals(msg.message, 'Some error text')
        assert_equals(msg.level, 'ERROR')
        assert_true(msg.timestamp.startswith('20'))


if __name__ == '__main__':
    unittest.main()
