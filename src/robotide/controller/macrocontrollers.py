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

import os
from itertools import chain

from .. import robotapi
from .arguments import parse_arguments_to_var_dict
from .basecontroller import ControllerWithParent, WithUndoRedoStacks
from .settingcontrollers import (DocumentationController, FixtureController, TagsController, TimeoutController,
                                 TemplateController, ArgumentsController, ReturnValueController)
from .stepcontrollers import ForLoopStepController, StepController, IntendedStepController
from .tags import Tag
from ..namespace.local_namespace import local_namespace
from ..publish.messages import (RideItemStepsChanged, RideItemNameChanged, RideItemSettingsChanged,
                                RideUserKeywordRemoved)
from ..spec.iteminfo import ResourceUserKeywordInfo, TestCaseUserKeywordInfo
from ..utils import variablematcher

KEYWORD_NAME_FIELD = 'Keyword Name'
TESTCASE_NAME_FIELD = 'Test Case Name'


def obtain_bdd_prefixes(language):
    from robotide.lib.compat.parsing.language import Language
    lang = Language.from_name(language[0] if isinstance(language, list) else language)
    bdd_prefixes = lang.bdd_prefixes
    return list(bdd_prefixes)

def _empty_step():
    return robotapi.Step([])


class ItemNameController(object):

    def __init__(self, item):
        self._item = item

    def contains_keyword(self, name):
        # print(f"DEBUG: macrocontrollers.py ItemNameController contains_keyword: item={self._item.name} search="
        #       f"{name}")
        if isinstance(name, str):
            return self._item.name == name
        return name.match(self._item.name)

    def contains_variable(self, name):
        return variablematcher.value_contains_variable(self._item.name, name)

    def replace_keyword(self, new_name, old_value=None):
        # print(f"DEBUG: macrocontrollers.py replace_keyword new_name={new_name} old_value={old_value}")
        self._item.rename(new_name)

    def rename(self, new_name):
        self._item.rename(new_name)

    def notify_value_changed(self, old_name=None, new_name=None):
        # print(f"DEBUG: macrocontrollers.py notify_value_changed item={self._item.name} old_name={old_name}")
        if not new_name:
            new_name=self._item.name
        self._item.notify_name_changed(old_name=old_name, new_name=new_name)

    @property
    def parent(self):
        return self._item


class KeywordNameController(ItemNameController):
    _name_field = KEYWORD_NAME_FIELD


class TestCaseNameController(ItemNameController):
    __test__ = False
    _name_field = TESTCASE_NAME_FIELD


class WithStepsController(ControllerWithParent, WithUndoRedoStacks):

    def __init__(self, parent_controller, data):
        self._parent = parent_controller
        self.data = data
        self._init(data)
        self._has_steps_changed = True
        self._steps_cached = None
        self.datafile_controller.register_for_namespace_updates(
            self.clear_cached_steps)

    @property
    def source(self):
        return os.path.basename(self.data.source) if self.data.source else ''

    @property
    def name(self):
        return self.data.name

    @property
    def steps(self):
        if self._has_steps_changed:
            self._recreate_steps()
        return self._steps_cached

    def set_parent(self, new_parent):
        self.clear_cached_steps()
        ControllerWithParent.set_parent(self, new_parent)

    def _recreate_steps(self):
        flattened_steps = []
        for step in self.data.steps:
            if step.is_for_loop():
                for_loop = ForLoopStepController(self, step)
                flattened_steps.append(for_loop)
                flattened_steps.extend(for_loop.steps)
            else:
                flattened_steps.append(StepController(self, step))
        self._steps_cached = flattened_steps
        self._has_steps_changed = False

    def clear_cached_steps(self):
        self._has_steps_changed = True
        self._steps_cached = None

    @property
    def max_columns(self):
        return max(chain((len(step) for step in self.steps), [0]))

    def has_template(self):
        return False

    def step(self, index):
        return self.steps[index]

    def index_of_step(self, step):
        return [s.step_controller_step for s in self.steps].index(step)

    def replace_step(self, index, new_step):
        corrected_index = index
        for i in range(index):
            if isinstance(self.step(i), IntendedStepController):
                corrected_index -= 1
        self.data.steps[corrected_index] = new_step
        self._has_steps_changed = True

    def move_step_up(self, index):
        self.step(index).move_up()
        self._has_steps_changed = True

    def move_step_down(self, index):
        self.step(index).move_down()
        self._has_steps_changed = True

    def set_steps(self, steps):
        self.data.steps = steps
        self._has_steps_changed = True

    def update_namespace(self):
        self.datafile_controller.update_namespace()

    def get_local_namespace(self):
        return local_namespace(self, self.datafile_controller.namespace)

    def get_local_namespace_for_row(self, row):
        # print(f"DEBUG: local namespace_for_row controller.namespace {self.datafile_controller.namespace} row {row}")
        return local_namespace(self, self.datafile_controller.namespace, row)

    def get_cell_info(self, row, col):
        steps = self.steps
        if row < 0 or len(steps) <= row:
            return None
        return steps[row].get_cell_info(col)

    def get_keyword_info(self, kw_name):
        return self.datafile_controller.keyword_info(None, kw_name)

    def is_user_keyword(self, value):
        return self.datafile_controller.is_user_keyword(None, value)

    def is_library_keyword(self, value):
        return self.datafile_controller.is_library_keyword(None, value)

    def delete(self):
        self.datafile_controller.unregister_namespace_updates(
            self.clear_cached_steps)
        self._parent.delete(self)
        self.notify_keyword_removed()

    def rename(self, new_name):
        # print(f"DEBUG: macrocontrollers.py WithStepsController rename BEFORE new_name={new_name} old_name={self.data.name}")
        self.data.name = new_name.strip()
        self.mark_dirty()

    def copy(self, name):
        new = self._parent.new(name)
        for orig, copied in zip(self.settings, new.settings):
            copied.set_from(orig)
        new.data.steps = [robotapi.Step(s.as_list()) for s in self.steps]
        new.notify_steps_changed()
        return new

    def get_empty_rows(self):
        return [index for index, step in enumerate(self.steps)
                if self._is_empty_step(step)]

    @staticmethod
    def _is_empty_step(step):
        return step.as_list() in [[], ['']]

    def remove_step(self, index):
        self._remove_step(self.steps[index])
        self._has_steps_changed = True

    def recreate(self):
        self._parent.add(self)

    def _remove_step(self, step):
        step.remove()
        self._has_steps_changed = True

    def add_step(self, index, step=None):
        # print(f"\nDEBUG: WithStepsController enter add_step step={step}")
        if step is None:
            step = _empty_step()
        if index == len(self.steps):
            self.data.steps.append(step)
        else:
            previous_step = self.step(index)
            previous_step.insert_before(step)
        self._has_steps_changed = True

    def create_keyword(self, name, argstr):
        name = self._remove_bdd_prefix(name)
        validation = self.datafile_controller.validate_keyword_name(name)
        if validation.error_message:
            raise ValueError(validation.error_message)
        return self.datafile_controller.create_keyword(name, argstr)

    def _remove_bdd_prefix(self, name):
        bdd_prefix = []
        language = self.language[0] if isinstance(self.language, list) else self.language
        if language and language.lower() not in ['en', 'english']:
            bdd_prefix = [f"{x.lower()} " for x in obtain_bdd_prefixes(language)]
        bdd_prefix += ['given ', 'when ', 'then ', 'and ', 'but ']
        # print(f"DEBUG: macrocontrollers.py WithStepsController _remove_bdd_prefix bdd_prefix={bdd_prefix}")
        matcher = name.lower()
        for match in bdd_prefix:
            if matcher.startswith(match):
                return name[len(match):]
        return name

    def create_test(self, name):
        return self.datafile_controller.create_test(name)

    def extract_keyword(self, name, argstr, step_range):
        extracted_steps = self._extract_steps(step_range)
        self._replace_steps_with_kw(name, step_range)
        self._create_extracted_kw(name, argstr, extracted_steps)

    def get_raw_steps(self):
        # Reveales inner state so can't be sure if cache is up-to-date
        self._has_steps_changed = True
        return self.data.steps

    def set_raw_steps(self, steps):
        self.set_steps(steps)

    def _extract_steps(self, step_range):
        rem_start, rem_end = step_range
        extracted_steps = self.steps[rem_start:rem_end + 1]
        return self._convert_controller_to_steps(extracted_steps)

    @staticmethod
    def _convert_controller_to_steps(step_controllers):
        return [robotapi.Step(s.as_list()) for s in step_controllers]

    def _replace_steps_with_kw(self, name, step_range):
        steps_before_extraction_point = self._convert_controller_to_steps(
            self.steps[:step_range[0]])
        extracted_kw_step = [robotapi.Step([name])]
        steps_after_extraction_point = self._convert_controller_to_steps(
            self.steps[step_range[1] + 1:])
        self.set_steps(steps_before_extraction_point + extracted_kw_step +
                       steps_after_extraction_point)

    def _create_extracted_kw(self, name, argstr, extracted_steps):
        controller = self.datafile_controller.create_keyword(name, argstr)
        controller.set_steps(extracted_steps)
        return controller

    def validate_name(self, name):
        return self._parent.validate_name(name, self)

    def notify_name_changed(self, old_name=None, new_name=None):
        self.update_namespace()
        self.mark_dirty()
        RideItemNameChanged(item=self, old_name=old_name, new_name=new_name).publish()

    def notify_keyword_removed(self):
        self.update_namespace()
        RideUserKeywordRemoved(datafile=self.datafile, name=self.name, item=self).publish()
        self.notify_steps_changed()

    def notify_settings_changed(self, old_name=None, new_name=None):
        _ = old_name
        _ = new_name
        self.update_namespace()
        self._notify(RideItemSettingsChanged)

    def notify_steps_changed(self, old_name=None):
        self._has_steps_changed = True
        # print(f"DEBUG: macrocontrollers.py WithStepsController notify_steps_changed: ENTER old_name={old_name}"
        #       f" {self.parent} {self.source} {self} call self._notify")
        self._notify(RideItemStepsChanged)

    def _notify(self, messageclass):
        self.mark_dirty()
        messageclass(item=self).publish()


class TestCaseController(WithStepsController):
    __test__ = False

    _populator = robotapi.TestCasePopulator
    filename = ""

    def _init(self, test):
        self._test = test
        self._run_passed = None

    def __eq__(self, other):
        if self is other:
            return True
        if other.__class__ != self.__class__:
            return False
        return self._test == other._test

    def __hash__(self):
        return hash(repr(self))

    @property
    def longname(self):
        return self.parent.parent.longname + '.' + self.data.name

    @property
    def test_name(self):
        return TestCaseNameController(self)

    @property
    def tags(self):
        return TagsController(self, self._test.tags)

    @property
    def force_tags(self):
        return self.datafile_controller.force_tags

    @property
    def test_tags(self):
        return self.datafile_controller.test_tags

    @property
    def default_tags(self):
        return self.datafile_controller.default_tags

    def add_tag(self, name):
        self.tags.add(Tag(name))

    @property
    def settings(self):
        return [
            self.documentation,
            FixtureController(self, self._test.setup),
            FixtureController(self, self._test.teardown),
            TimeoutController(self, self._test.timeout),
            TemplateController(self, self._test.template),
            self.tags
        ]

    @property
    def documentation(self):
        return DocumentationController(self, self._test.doc)

    def move_up(self):
        return self._parent.move_up(self._test)

    def move_down(self):
        return self._parent.move_down(self._test)

    def validate_test_name(self, name):
        return self._parent.validate_name(name)

    def validate_keyword_name(self, name):
        return self.datafile_controller.validate_keyword_name(name)

    @staticmethod
    def get_local_variables():
        return {}

    def has_template(self):
        template = self._get_template()
        if not template:
            return False
        return bool(template.value)

    def _get_template(self):
        template = self._test.template
        if template.value is not None:
            return template
        return self.datafile_controller.get_template()

    @property
    def run_passed(self):
        return self._run_passed

    @run_passed.setter
    def run_passed(self, value):
        if value not in [True, False, None]:
            self._run_passed = None  # Test did not run
        if value:
            self._run_passed = True  # Test execution passed
        else:
            self._run_passed = False  # Test execution failed


class UserKeywordController(WithStepsController):
    _populator = robotapi.UserKeywordPopulator
    _TEARDOWN_NOT_SET = object()
    _teardown = _TEARDOWN_NOT_SET
    _SETUP_NOT_SET = object()
    _setup = _SETUP_NOT_SET

    def _init(self, kw):
        self.kw = kw
        # Needed for API compatibility in tag search
        self.force_tags = []
        self.default_tags = []
        self.test_tags = []

    def __eq__(self, other):
        if self is other:
            return True
        if other.__class__ != self.__class__:
            return False
        return self.kw == other.kw

    def __hash__(self):
        return hash(repr(self))

    @property
    def info(self):
        if isinstance(self.datafile, robotapi.ResourceFile):
            return ResourceUserKeywordInfo(self.data)
        return TestCaseUserKeywordInfo(self.data)

    @property
    def keyword_name(self):
        return KeywordNameController(self)

    def move_up(self):
        return self._parent.move_up(self.kw)

    def move_down(self):
        return self._parent.move_down(self.kw)

    @property
    def settings(self):
        result = [
            DocumentationController(self, self.kw.doc),
            ArgumentsController(self, self.kw.args),
            self.setup,
            self.teardown,
            ReturnValueController(self, self.kw.return_),
            TimeoutController(self, self.kw.timeout),
            TagsController(self, self.kw.tags),
        ]
        return result

    @property
    def setup(self):
        if self._setup == self._SETUP_NOT_SET:
            self._setup = FixtureController(self, self.kw.setup_)
        return self._setup

    @property
    def teardown(self):
        if self._teardown == self._TEARDOWN_NOT_SET:
            self._teardown = FixtureController(self, self.kw.teardown)
        return self._teardown

    @property
    def arguments(self):
        return ArgumentsController(self, self.kw.args)

    def validate_keyword_name(self, name):
        return self._parent.validate_name(name)

    def get_local_variables(self):
        return parse_arguments_to_var_dict(self.kw.args.value, self.kw.name)
