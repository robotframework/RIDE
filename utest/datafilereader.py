import os
from robotide.controller.chiefcontroller import ChiefController
from robotide.namespace import Namespace
RESOURCES_DIR = 'resources'
RESOURCES_HTML = 'resource.html'
DATAPATH = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 
                        RESOURCES_DIR, 'robotdata')

def _makepath(*elements):
    elements = [DATAPATH]+list(elements)
    return os.path.normpath(os.path.join(*elements)).replace('\\', '/')

RESOURCE_PATH = _makepath(RESOURCES_DIR, RESOURCES_HTML)
RESOURCE_LIB_PATH = _makepath(RESOURCES_DIR, 'resource_lib_imports.txt')
RESOURCE_WITH_VARS = _makepath(RESOURCES_DIR, 'resource_with_variables.txt')
TESTCASEFILE_WITH_EVERYTHING = _makepath('testsuite', 'everything.html')
RELATIVE_IMPORTS = _makepath('relative_imports', 'relative.txt')
LOG_MANY_SUITE = _makepath('logmanysuite', 'log_many.txt')
KW1000_TESTCASEFILE = _makepath('performance', 'suite_kw1000.txt')
KW2000_TESTCASEFILE = _makepath('performance', 'suite_kw2000.txt')
KW3000_TESTCASEFILE = _makepath('performance', 'suite_kw3000.txt')
KW4000_TESTCASEFILE = _makepath('performance', 'suite_kw4000.txt')
RESOURCE_WITH_VARIABLE_IN_PATH = _makepath(RESOURCES_DIR, 'resu.${extension}')
LIBRARY_WITH_SPACES_IN_PATH = _makepath('lib with spaces', 'spacelib.py')
TESTCASEFILE_WITH_RESOURCES_WITH_VARIABLES_FROM_VARIABLE_FILE = _makepath('var_file_variables',
                                            'import_resource_with_variable_from_var_file.txt')

OCCURRENCES_RESOURCE_NAME = 'Testdata Resource'
OCCURRENCES_RESOURCE_FILE = 'testdata_resource.txt'
OCCURRENCES_PATH = _makepath('simple_testsuite_with_different_namespaces')

ARGUMENTS_PATH = _makepath('arguments_suite')

def construct_chief_controller(datapath):
    class NullObserver(object):
        def notify(self, *args):
            pass
    
        def finish(self, *args):
            pass
        
    chief = ChiefController(Namespace())
    chief.load_data(datapath, NullObserver())
    return chief

def get_ctrl_by_name(name, datafiles):
    for file in datafiles:
        if file.name == name:
            return file
    return None