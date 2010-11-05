import os
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
RESOURCE_WITH_VARIABLE_IN_PATH = _makepath(RESOURCES_DIR, 'resu.${extension}')
LIBRARY_WITH_SPACES_IN_PATH = _makepath('lib with spaces', 'spacelib.py')
TESTCASEFILE_WITH_RESOURCES_WITH_VARIABLES_FROM_VARIABLE_FILE = _makepath('var_file_variables',
                                            'import_resource_with_variable_from_var_file.txt')
OCCURRENCES_PATH = _makepath('occurrences')