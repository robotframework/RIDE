Language: English

*** Settings ***
Suite Setup  Run Keywords  Suite Setup Keyword  AND  First KW
Test Teardown  Run Keywords  Test Teardown in Setting  AND  Second KW

*** Test Cases ***
My Test
  [Teardown]  Run Keywords  Second KW  AND  Test Teardown Keyword
  Log  Local

My Other Test
  [Setup]  Run Keywords  First KW  AND  Test Setup Keyword
  Second KW

My Third Test
  [Setup]  Run Keyword  Test Setup Keyword
  [Teardown]  Run Keyword  Test Teardown Keyword
  No Operation

*** Keywords ***
First KW
  [Documentation]  First Keyword
  No Operation

Second KW
  [Documentation]  Second Keyword
  No Operation

Test Setup Keyword
  [Teardown]  Keyword Teardown Keyword
  No Operation

Test Teardown Keyword
  No Operation

Keyword Teardown Keyword
  No Operation

Suite Setup Keyword
  First KW

Test Teardown in Setting
  Second KW
  No Operation

