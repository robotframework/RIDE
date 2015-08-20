import unittest
from nose.tools import assert_equals

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
        print ctx.vars
        assert_equals(result, "!moi!hoi!['koi']!")

if __name__ == '__main__':
    unittest.main()
