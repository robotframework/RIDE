import unittest
from nose.tools import assert_equals

from robotide.run.runanything import RunConfigs


ITEM = ('name', 'command', 'doc')


class RunConfigurationsTest(unittest.TestCase):

    def test_creation_with_no_data(self):
        configs = RunConfigs([])
        assert_equals(len(configs), 0)

    def test_creation_with_data(self):
        self._assert_config(self._create_configs_with_item()[0], *ITEM)

    def test_adding(self):
        item = ('newname', 'some command', '')
        self._assert_config(RunConfigs([]).add(*item), *item)

    def test_edit(self):
        configs = self._create_configs_with_item()
        configs.edit(0, 'edited_name', 'cmd', 'doc')
        self._assert_config(configs[0], 'edited_name', 'cmd', 'doc')

    def test_update(self):
        items = [ITEM, ('another', 'ls -l', '')]
        edited = [('Changed Name', 'command', 'doc'),
                  ('', '', '')]
        configs = RunConfigs(items)
        configs.update(edited)
        self._assert_config(configs[0], 'Changed Name', 'command', 'doc')
        self._assert_config(configs[1], '', '' ,'')

    def test_data_to_save(self):
        configs = self._create_configs_with_item()
        assert_equals(configs.data_to_save(), [ITEM])

    def _create_configs_with_item(self):
        return RunConfigs([ITEM])

    def _assert_config(self, config, exp_name, exp_cmd, exp_doc):
        assert_equals(config.name, exp_name)
        assert_equals(config.command, exp_cmd)
        assert_equals(config.doc, exp_doc)

