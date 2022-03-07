*** Settings ***
Documentation  suitedocmatch
Resource    testdata_resource.robot
Suite Setup  Run Keyword  Suite Setup Keyword
Test Teardown  Test Teardown in Setting

*** Variables ***
@{Test Suite 2 List}  2  3
${Test Suite 2 Var}  irobota

*** Test Cases ***
My Test
  [Documentation]  testdocmatch
  My Keyword
  My Keyword
  None Keyword
  Log  Local

My Other Test
  None Keyword
  None Keyword

My Third Test
  [Setup]  Run Keyword  Test Setup Keyword
  [Teardown]  Run Keyword  Test Teardown Keyword
  No Operation

*** Keywords ***
Log
  [Documentation]  keyworddocmatch
  Overrides builtin

Test Setup Keyword
  [Teardown]  Keyword Teardown Keyword
  No Operation

Test Teardown Keyword
  No Operation

Keyword Teardown Keyword
  No Operation

Suite Setup Keyword
  No Operation

Test Teardown in Setting
  No Operation
