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
from nose.tools import assert_equal

from robotide.namespace.namespace import _RetrieverContextFactory
from robotide.robotapi import ResourceFile


def datafileWithVariables(vars):
    data = ResourceFile()
    for var in vars:
        data.variable_table.add(var, vars[var])
    return data


class RetrieverContextFactoryTest(unittest.TestCase):

    def test_created_context_has_variable_table_variables(self):
        factory = _RetrieverContextFactory()
        ctx = factory.ctx_for_datafile(
            datafileWithVariables({'${foo}': 'moi', '${bar}': 'hoi',
                                   '@{zoo}': 'koi'}))
        result = ctx.vars.replace_variables('!${foo}!${bar}!@{zoo}!')
        print(ctx.vars)
        assert_equal(result, "!moi!hoi!['koi']!")

if __name__ == '__main__':
    unittest.main()
