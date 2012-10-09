#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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
from math import ceil
import os
import random
import shutil
import time
import sys
import sqlite3
from sqlite3 import OperationalError
import copy


ROOT = os.path.dirname(__file__)
lib = os.path.join(ROOT, '..', 'lib')
src = os.path.join(ROOT, '..', 'src')

sys.path.insert(0, lib)
sys.path.insert(0, src)

from model import RIDE
from test_runner import Runner

start_time = None
end_time = None

db_connection = None
db_cursor = None

verbs = ['do','make','execute','select','count','process','insert','validate','verify']
words = None

def _create_test_libraries(path, filecount = 10, keywords=10):
    global db_cursor, verbs, words

    libs = []

    for x in range(filecount):
        lib_main = random.choice(words).strip().capitalize()
        lib_name = "CustomLib%s" % lib_main
        libs.append(lib_name)
        db_cursor.execute("INSERT INTO source (path,type) VALUES ('%s','CUSTOMLIBRARY')" % lib_name)
        libfile = open("%s/%s.py" % (path,lib_name),"w")
        libfile.write(\
"""
import os,time

class %s:
    def __init__(self):
""" % lib_name)

        directory_looper = """\tfor dirname, dirnames, filenames in os.walk('.'):
            for subdirname in dirnames:
                print os.path.join(dirname, subdirname)
            for filename in filenames:
                print os.path.join(dirname, filename)"""
        sleeper = "\ttime.sleep(2)"

        libfile.write(random.choice([directory_looper, sleeper]) + "\n")

        temp_verb = copy.copy(verbs)
        counter = 1
        for x in range(keywords):
            if len(temp_verb) > 0:
                verb = temp_verb.pop().capitalize()
            else:
                verb = "KW_%d" % counter
                counter += 1
            kw_name = verb + "_" + lib_main
            db_cursor.execute("INSERT INTO keywords (name,source) VALUES ('%s','%s')" % (kw_name,lib_name))
            libfile.write(\
"""
    def %s():
        pass
""" % kw_name)

        libfile.write(\
"""
myinstance = %s()
""" % lib_name)
        libfile.close()

    initfile_lines = open("%s/__init__.txt" % path).readlines()
    index = 0
    for line in initfile_lines:
        if "*** Settings ***" in line:
            index += 1
            for lib_name in libs:
                initfile_lines.insert(index, "Library\t%s.py\n" % (os.getcwd() + "/" + path + "/" + lib_name))
                index += 1
            break
        index += 1

    fo = open("%s/__init__.txt" % path, "w")
    for line in initfile_lines:
        fo.write(line)
    fo.close()


def _create_test_suite(path, filecount = 1, testcount = 20):
    global db_cursor, verbs, words

    available_resources = db_cursor.execute(
                            "SELECT path FROM source WHERE type = 'RESOURCE' ORDER BY RANDOM()").fetchall()

    for testfile_index in range(filecount):
        libraries_in_use = {}
        resources_in_use = []

        settings_txt = ""
        test_txt = ""
        keywords_txt = ""
        available_libraries = db_cursor.execute("SELECT path FROM source WHERE type = 'CUSTOMLIBRARY'").fetchall()

        tcfile = open("%s/CustomTests_%d.txt" % (path, testfile_index+1),"w")
        test_txt += "*** Test Cases ***\n"
        for tc in range(testcount):
            selected_library = random.choice(available_libraries)[0]
            tc_withname = None
            if selected_library not in libraries_in_use.values():
                tc_withname = "Cus%d" % tc
                libraries_in_use[tc_withname] = selected_library
            else:
                for key,val in libraries_in_use.iteritems():
                    if val == selected_library:
                        tc_withname = key
                        break
            tc_name = "Test %s in %s #%d" % (random.choice(verbs), selected_library.split("CustomLib")[1], tc)
            available_keywords = db_cursor.execute("SELECT * FROM keywords WHERE source = '%s' ORDER BY RANDOM()"
                                                    % selected_library).fetchall()
            kwlib = random.choice([selected_library, tc_withname, tc_withname + "xyz"])
            kw1 = available_keywords.pop()
            kw2 = available_keywords.pop()
            test_txt += "%s\t[Documentation]\t%s\n\t\t%s\n\t\t%s\n\n" % (tc_name, "Test %d" % tc, kwlib +
                    "." +kw1[1].replace("_"," "), kwlib + "." +kw2[1].replace("_"," "))

        settings_txt += "*** Settings ***\n"
        for tc_withname,tc_name in libraries_in_use.iteritems():
            settings_txt += "Library    %45s.py\tWITH NAME\t%s\n" % (tc_name, tc_withname)
            #settings_txt += "Library    %45s\n" % (os.getcwd()+"/"+path+"/" +tc_name)

        for x in range(random.randint(0,2)):
            try:
                selected_resource = available_resources.pop()[0]
                settings_txt += "Resource   %45s\n" % selected_resource
            except IndexError:
                break
        settings_txt += "\n"
        keywords_txt += "*** Keywords ***\n"
        keywords_txt += "My Keyword\n\tNo Operation\n"
        tcfile.write(settings_txt)
        tcfile.write(test_txt)
        tcfile.write(keywords_txt)
        tcfile.close()


def _create_test_resources(path, filecount, resource_count):
    global db_cursor, verbs, words

    for resfile_index in range(filecount):
        resource_name = "%s/Resource_%d.txt" % (path, resfile_index+1)
        resfile = open(resource_name,"w")
        content = "*** Settings ***\n"
        #available_keywords = db_cursor.execute("SELECT * FROM keywords ORDER BY RANDOM()").fetchall()
        content += "\n*** Variables ***\n"
        for x in range(resource_count):
            content += "%-25s%10s%d\n" % ("${%s%d}" % (random.choice(words).strip().capitalize(),x),"",
                                                        random.randint(1,1000))
        content += "\n*** Keywords ***\n"
        resfile.write(content)
        resfile.close()
        db_cursor.execute("INSERT INTO source (path,type) VALUES ('%s','RESOURCE')" % resource_name)


def _create_test_project(path,testlibs_count=5,keyword_count=10,testsuite_count=5,tests_in_suite=10,resource_count=10,resources_in_file=20):
    shutil.rmtree(path, ignore_errors=True)
    thetestdir = os.path.join(path, 'testdir')
    shutil.copytree(os.path.join(ROOT, 'testdir'), thetestdir)

    print """Generating test project with following settings
    %d test libraries (option 'l')
    %d keywords per test library (option 'k')
    %d test suites (option 's')
    %d tests per test suite (option 't')
    %d resource files (option 'f')
    %d resources per resource file (option 'r')""" % (testlibs_count, keyword_count, testsuite_count,
                                        tests_in_suite, resource_count, resources_in_file)

    _create_test_libraries(thetestdir, filecount=testlibs_count, keywords=keyword_count)
    _create_test_resources(thetestdir + "/resources", filecount=resource_count,resource_count=resources_in_file)
    _create_test_suite(thetestdir, filecount=testsuite_count, testcount=tests_in_suite)

def main(path,testlibs_count=25,keyword_count=10,testsuite_count=30,tests_in_suite=40,resource_count=10,resources_in_file=100):
    global db_connection, db_cursor, words

    words = open("testwords.txt").readlines()

    db_connection=sqlite3.connect("testdata.db")
    db_cursor=db_connection.cursor()
    try:
        db_cursor.execute('CREATE TABLE IF NOT EXISTS source (id INTEGER PRIMARY KEY, path TEXT, type TEXT)')
        db_cursor.execute('CREATE TABLE IF NOT EXISTS keywords (id INTEGER PRIMARY KEY, name TEXT, source TEXT, arguments INTEGER, returns INTEGER)')
        db_cursor.execute('DELETE FROM source')
        db_cursor.execute('DELETE FROM keywords')
        libs_to_insert = [("BuiltIn","LIBRARY"),("OperatingSystem","LIBRARY"),("String","LIBRARY")]
        db_cursor.executemany('INSERT INTO source (path,type) VALUES (?,?)', libs_to_insert)
        keywords_to_insert = [("Log","BuiltIn",1,0),("No Operation","BuiltIn",0,0),("Get Time","BuiltIn",0,1),
                              ("Count Files In Directory","Operating System",0,1),("Get Environment Variables","BuiltIn",0,1),
                              ("Get Time","BuiltIn",0,1)]
        db_cursor.executemany('INSERT INTO keywords (name,source,arguments,returns) VALUES (?,?,?,?)', keywords_to_insert)
        db_connection.commit()
    except OperationalError, err:
        print "DB error: ",err

    _create_test_project(path,testlibs_count,keyword_count,testsuite_count,tests_in_suite,resource_count,resources_in_file)
    result = "PASS"
    return result != 'FAIL'

if __name__ == '__main__':
    if not main(sys.argv[1]):
        print 'error occurred!'
        sys.exit(1) #indicate failure