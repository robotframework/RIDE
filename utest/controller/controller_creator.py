from robotide.robotapi import(
    TestCaseFile, TestDataDirectory, FromFilePopulator)
from robotide.controller.basecontroller import WithNamespace
from robotide.controller.filecontrollers import TestCaseFileController,\
    TestDataDirectoryController

TEST_NAME = 'Test With two Steps'
STEP1_KEYWORD = 'Step 1'
STEP1 = '  '+STEP1_KEYWORD+'  arg'
STEP2 = '  Step 2  a1  a2  a3'
STEP_WITH_COMMENT = '  Foo  # this is a comment'
FOR_LOOP_HEADER = '  : FOR  ${i}  IN  1  2  3'
FOR_LOOP_STEP1 = '    Log  ${i}'
FOR_LOOP_STEP2 = '    No Operation'
STEP_AFTER_FOR_LOOP = '  Step bar'

BASE_DATA = [TEST_NAME,
        STEP1,
        STEP2,
        STEP_WITH_COMMENT,
        FOR_LOOP_HEADER,
        FOR_LOOP_STEP1,
        FOR_LOOP_STEP2,
        STEP_AFTER_FOR_LOOP,
        '  ${variable}=  some value'
]

class _FakeProject(WithNamespace):

    def update_namespace(self):
        pass

    def register_for_namespace_updates(self, listener):
        pass

    def unregister_namespace_updates(self, listener):
        pass

    resource_file_controller_factory = None

def create(data):
    tcf = TestCaseFile()
    tcf.directory = '/path/to'
    pop = FromFilePopulator(tcf)
    pop.start_table(['Test cases'])
    for row in [ [cell for cell in line.split('  ')] for line in data]:
        pop.add(row)
    pop.eof()
    return tcf


def testcase_controller(project=None, data=None):
    if data is None:
        data = BASE_DATA[:]
    base_directory_controller = TestDataDirectoryController(TestDataDirectory(), project)
    directory_controller = TestDataDirectoryController(TestDataDirectory(), project, base_directory_controller)
    tcf_controller = TestCaseFileController(create(data), project, directory_controller)
    tctablectrl = tcf_controller.tests
    return tctablectrl[0]
