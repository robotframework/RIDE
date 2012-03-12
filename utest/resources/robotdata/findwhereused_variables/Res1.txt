*** Variables ***
${resVar}         "something"
${anotherVar}     "Nothing but ${EMPTY} ${SPACE}"

*** Keywords ***
User KW 1
    [Arguments]    ${arg1}    @{arg2}
    ${ServerPort}
    ${True}    ${False}
    [Teardown]    ${resVar}

User KW 2
    [Arguments]    ${arg1}    @{arg2}
    [Documentation]    Lorem ${arg1} ipsum
    Log    ${resVar}
    ${arg1}
    @{arg2}
    [Teardown]    @{arg2}

