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

import builtins
from wx import GetTranslation
from ..robotapi import ALIAS_MARKER

_ = GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = GetTranslation

PH_ESCAPE ="%(ESCAPE)s"  # PH = Place Holder
INHERIT_TAG = "Inherited tags are not shown in this view."
PH_TAGS = "%(TAG)s"
PH_FIXTURE = "%(FIXTURE)s"

def get_help(title):
    _HELPS = {}
    _EXAMPLES = {
        'ESCAPE': _("Possible pipes in the value must be escaped with a backslash like '\\|'."),
        'TAG': _("Separate tags with a pipe character like 'tag | second tag | 3rd'."),
        'FIXTURE': _("Separate possible arguments with a pipe character like 'My Keyword | arg 1 | arg 2'."),
        'TIMEOUT': _("Use time syntax like '1min 10s' or '2 hours' or give the value as seconds.\n"
                     "Before Robot v3.0.1 an optional message could have been specified like "
                     "'3 minutes | My message here'."),
        'ARGUMENTS': _("Specify the arguments separated with a pipe character like '${arg1} | ${arg2}'.\n"
                       "Default values are given using equal sign and the last argument can be a list variable.\n"
                       "Example: '${arg1} | ${arg2}=default value | @{rest}'.\n"
                       "Note. You can use variable shortcuts in this field."),
        'ALIAS': _("Alias can be used to import same library multiple times with different names.\n"
                   "Alias is prepended with: ") + ALIAS_MARKER +
        _(" . Note that since Robot v6.0, imports with old WITH NAME are replaced by AS.")
    }
    content = ['', "Scalar Variable", _("Give name and value of the variable."), '', "List Variable",
               _("Give name and value of the variable. Input list variable items into separate cells."), '',
               "Dictionary Variable",
               _("Give name and value of the variable. Input dictionary items into separate cells."),
               _("Individual items must be in format `key=value`"), '', "Library",
               _("Give name, optional arguments and optional alias of the library to import."),
               _("Separate multiple arguments with a pipe character like 'arg 1 | arg 2'."), "%(ALIAS)s", '',
               "Variables", _("Give path and optional arguments of the variable file to import."),
               _("Separate multiple arguments with a pipe character like 'arg 1 | arg 2'."), PH_ESCAPE, '',
               "Resource", _("Give path to the resource file to import."),
               _("Existing resources will be automatically loaded to the resource tree."),
               _("New resources must be created separately."), '', "Documentation", _("Give the documentation."),
               _("Simple formatting like *bold* and _italic_ can be used."),
               _("Additionally, URLs are converted to clickable links."), '', "Force Tags",
               _("These tags are set to all test cases in this test suite."),
               _(INHERIT_TAG), PH_TAGS, PH_ESCAPE, '', "Default Tags",
               _("These tags are set to all test cases in this test suite unless test cases have their own tags."),
               PH_TAGS, PH_ESCAPE, '', "Test Tags",
               _("These tags are applied to all test cases in this test suite. "
                 "This field exists since Robot Framework 6.0 and will replace "
                 "Force and Default Tags after version 7.0."), _(INHERIT_TAG),
               PH_TAGS, PH_ESCAPE, '', "Tags",
               _("These tags are set to this test case in addition to "
                 "Force Tags and they override possible Default Tags."),
               _(INHERIT_TAG), PH_TAGS, PH_ESCAPE, '', "Suite Setup",
               _("This keyword is executed before executing any of the test cases or lower level suites."),
               PH_FIXTURE, PH_ESCAPE, '', "Suite Teardown",
               _("This keyword is executed after all test cases and lower level suites have been executed."),
               PH_FIXTURE, PH_ESCAPE, '', "Test Setup",
               _("This keyword is executed before every test case in this suite unless test cases override it."),
               PH_FIXTURE, PH_ESCAPE, '', "Test Teardown",
               _("This keyword is executed after every test case in this suite unless test cases override it."),
               PH_FIXTURE, PH_ESCAPE, '', "Setup",
               _("This keyword is executed before other keywords in this test case or keyword."),
               _("In test cases, overrides possible Test Setup set on the suite level."),
               _("Setup in keywords exists since Robot v7.0."), PH_FIXTURE, PH_ESCAPE, '', "Teardown",
               _("This keyword is executed after other keywords in this test case or keyword even if the test or "
                 "keyword fails."),
               _("In test cases, overrides possible Test Teardown set on the suite level."),
               PH_FIXTURE, PH_ESCAPE, '', "Test Template",
               _("Specifies the default template keyword used by tests in this suite."),
               _("The test cases will contain only data to use as arguments to that keyword."), '', "Template",
               _("Specifies the template keyword to use."),
               _("The test itself will contain only data to use as arguments to that keyword."), '', "Arguments",
               "%(ARGUMENTS)s", PH_ESCAPE, '', "Return Value",
               _("Specify the return value. Use a pipe character to separate multiple values."), PH_ESCAPE,
               "The '[Return]' setting is deprecated since Robot v7.0. Use the 'RETURN' statement instead.", '',
               "Test Timeout",
               _("Maximum time test cases in this suite are allowed to execute before aborting them forcefully."),
               _("Can be overridden by individual test cases using Timeout setting."), "%(TIMEOUT)s", '', "Timeout",
               _("Maximum time this test/keyword is allowed to execute before aborting it forcefully."),
               _("With test cases this setting overrides Test Timeout set on the suite level."), "%(TIMEOUT)s", '',
               "Metadata", _("Give a name and a value for the suite metadata."), '', "New Test Case",
               _("Give a name for the new test case."), '', "New User Keyword",
               _("Give a name and arguments for the new user keyword."), "%(ARGUMENTS)s", '',
               "Copy User Keyword", _("Give a name for the new user keyword.")]
    current = None
    for row in content:
        row = row.strip()
        if not row:
            current = None
        elif current is None:
            current = _HELPS.setdefault(row, [])
        else:
            current.append(row % _EXAMPLES)

    return '\n'.join(_HELPS[title])
