*** Settings ***
Resource        resources${/}resu.txt
Resource        generated_resut.txt
Library         String

*** Test Cases ***
Test Case 1
    Some local keyword  with  arguments
    No Operation
    Some keyword from resource file  2
    Should Be Empty  ${EMPTY}  5
    None Existing Keyword
    FOR  ${i}  IN RANGE  1000
      Log  ${i}
    END

Templated Test Case
    [Template]  Log
    Hello
    World

*** Keywords ***
Some local keyword
    [Arguments]  ${arg1}  ${arg2}
    Log  This is local ${arg1} for ${arg2}
    FOR  ${kekkonen}  IN  1  2  3
      Log  ${kekkonen}  ${EMPTY}  ${EMPTY}  NOT ALLOWED!!
    END
    ${value}=  Set Variable  4
    Replace String Using Regexp  ${arg1}  ${arg2}  replacee  7
    [Return]  65
