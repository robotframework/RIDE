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

from robotide.run.runanything import RunConfigs


ITEM = ('name', 'command', 'doc')


class RunConfigurationsTest(unittest.TestCase):

    def test_creation_with_no_data(self):
        configs = RunConfigs([])
        assert len(configs) == 0

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
        assert configs.data_to_save() == [ITEM]

    def _create_configs_with_item(self):
        return RunConfigs([ITEM])

    def _assert_config(self, config, exp_name, exp_cmd, exp_doc):
        assert config.name == exp_name
        assert config.command == exp_cmd
        assert config.doc == exp_doc


if __name__ == '__main__':
    unittest.main()

