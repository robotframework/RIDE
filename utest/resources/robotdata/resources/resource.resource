*** Settings ***
Resource          resource2.robot
Resource          resource3.robot
Resource          resource.robot

*** Variables ***
${RESOURCE var}    Foo

*** Keywords ***
Resource UK
    [Documentation]    This is a user keyword from resource file
    [Timeout]
    No Operation

Parametrized UK
    [Arguments]    ${arg}    ${defarg}=def val    @{vararg}
    [Timeout]
    Log Many    ${arg}    ${defarg}    @{vararg}

Funny Def Value
    [Arguments]    ${arg}=${None}    ${urg}=${myvar=foo}
    [Timeout]
    Log Many    ${arg}    ${urg}

Duplicate UK
    No Operation

User ${action} Email
    Log    Keyword call is "User ${action} Email"    console=True

Server ${action} To User
    [Arguments]    ${user}
    Log    Keyword call is "Server ${action} To User" where \${user}=${user}    console=True
