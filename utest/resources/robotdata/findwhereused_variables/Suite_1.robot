*** Settings ***
Variables         vars.py

*** Variables ***
${fileVar}        "nothing"

*** Test Cases ***
Case 1
    [Setup]    Some Keyword    ${fileVar}
    [Timeout]
    ${ServerHost}    ${ServerPort}
    ${False}

Case 2
    [Documentation]    The variable ${log} can be found here
    ${log}=    Set Variable    "Text"
    Log    ${log}
    ${ServerHost}
    [Teardown]    ${fileVar}

Case 3
    [Documentation]    The variable ${log} can also be found here
    Log    ${fileVar}
    ${EMPTY}

