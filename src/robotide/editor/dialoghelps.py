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


def get_help(title):
    return '\n'.join(_HELPS[title])


_HELPS = {}
_EXAMPLES = {
'ESCAPE': "Possible pipes in the value must be escaped with a backslash like '\|'.",
'TAG': "Separate tags with a pipe character like 'tag | second tag | 3rd'.",
'FIXTURE': "Separate possible arguments with a pipe character like 'My Keyword | arg 1 | arg 2'.",
'TIMEOUT': ("Use time syntax like '1min 10s' or '2 hours' or give the value as seconds.\n"
            "Optional message can be specified like '3 minutes | My message here'."),
'ARGUMENTS': ("Specify the arguments separated with a pipe character like '${arg1} | ${arg2}'.\n"
              "Default values are given using equal sign and the last argument can be a list variable.\n"
              "Example: '${arg1} | ${arg2}=default value | @{rest}'.\n"
              "Note. You can use variable shortcuts in this field.")
}

for row in """
Scalar Variable
Give name and value of the variable.

List Variable
Give name and value of the variable. Input list variable items into separate cells.

Dictionary Variable
Give name and value of the variable. Input dictionary items into separate cells.
Individual items must be in format `key=value`

Library
Give name, optional arguments and optional alias of the library to import.
Separate multiple arguments with a pipe character like 'arg 1 | arg 2'.
Alias can be used to import same library multiple times with different names.

Variables
Give path and optional arguments of the variable file to import.
Separate multiple arguments with a pipe character like 'arg 1 | arg 2'.
%(ESCAPE)s

Resource
Give path to the resource file to import.
Existing resources will be automatically loaded to the resource tree.
New resources must be created separately.

Documentation
Give the documentation.
Simple formatting like *bold* and _italic_ can be used.
Additionally, URLs are converted to clickable links.

Force Tags
These tags are set to all test cases in this test suite.
Inherited tags are not shown in this view.
%(TAG)s
%(ESCAPE)s

Default Tags
These tags are set to all test cases in this test suite unless test cases have their own tags.
%(TAG)s
%(ESCAPE)s

Tags
These tags are set to this test case in addition to Force Tags and they override possible Default Tags.
Inherited tags are not shown in this view.
%(TAG)s
%(ESCAPE)s

Suite Setup
This keyword is executed before executing any of the test cases or lower level suites.
%(FIXTURE)s
%(ESCAPE)s

Suite Teardown
This keyword is executed after all test cases and lower level suites have been executed.
%(FIXTURE)s
%(ESCAPE)s

Test Setup
This keyword is executed before every test case in this suite unless test cases override it.
%(FIXTURE)s
%(ESCAPE)s

Test Teardown
This keyword is executed after every test case in this suite unless test cases override it.
%(FIXTURE)s
%(ESCAPE)s

Setup
This keyword is executed before other keywords in this test case.
Overrides possible Test Setup set on the suite level.
%(FIXTURE)s
%(ESCAPE)s

Teardown
This keyword is executed after other keywords in this test case even if the test fails.
Overrides possible Test Teardown set on the suite level.
%(FIXTURE)s
%(ESCAPE)s

Test Template
Specifies the default template keyword used by tests in this suite.
The test cases will contain only data to use as arguments to that keyword.

Template
Specifies the template keyword to use.
The test itself will contain only data to use as arguments to that keyword.

Arguments
%(ARGUMENTS)s
%(ESCAPE)s

Return Value
Specify the return value. Use a pipe character to separate multiple values.
%(ESCAPE)s

Test Timeout
Maximum time test cases in this suite are allowed to execute before aborting them forcefully.
Can be overridden by individual test cases using Timeout setting.
%(TIMEOUT)s

Timeout
Maximum time this test/keyword is allowed to execute before aborting it forcefully.
With test cases this setting overrides Test Timeout set on the suite level.
%(TIMEOUT)s

Metadata
Give a name and a value for the suite metadata.

New Test Case
Give a name for the new test case.

New User Keyword
Give a name and arguments for the new user keyword.
%(ARGUMENTS)s

Copy User Keyword
Give a name for the new user keyword.
""".splitlines():
    row = row.strip()
    if not row:
        current = None
    elif current is None:
        current = _HELPS.setdefault(row, [])
    else:
        current.append(row % _EXAMPLES)
