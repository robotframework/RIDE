@echo off
rem Find pom.xml for this testsuite
setlocal EnableDelayedExpansion
rem Get path from first parameter
set return_path=%1
rem Check that dir contains pom.xml
if exist !return_path!\pom.xml goto continue
echo No pom.xml found in !return_path!
exit /B 1
:continue
rem Start maven
cd /D%return_path%
mvn -Prun-tests-with-ride verify -Dride.argumentFile=%3 -Dride.listener=%5 -Dride.testCasesDirectory=%6