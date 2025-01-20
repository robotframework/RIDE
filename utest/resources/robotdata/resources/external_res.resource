*** Settings ***
Documentation     This resource is to be used as external resource from test suite ../TestCases
Resource          ../TestCases/Sub/resources/res02.resource

*** Variables ***
${EXT_VARIABLE}    external variable    # from external resource

*** Keywords ***
keyword1
    [Arguments]    ${a}
    log    ${a}

keyword2
    [Arguments]    ${a}
    log    ${a}
    Log To Console    This is the argument \${a} = ${a} !
    [Teardown]    keyword1    Called from external_resource at Teardown kw2

keyword3
    [Setup]    res02.keyword3
    keyword1    Called from external_resource
    res02.keyword1    Called from external_resource    # Kw from res2 with a space in calling

unusedkw
    [Arguments]    ${notused}=None
    Log    This is not used
