Language: English

*** Settings ***
Library           AnotherArgLib    ${param1}    ${param1} here too: ${param2}    ${param2}

*** Variables ***
@{RESOURCE 2 List VARIABLE}    1    2    3    4
${param1}         An interesting value
${param2}         Hello

*** Keywords ***
Resource2 UK
    [Timeout]
    No Operation

My Suite Setup
    No Operation

My Suite Teardown
    [Arguments]    @{args}
    No Operation

My Overriding Test Setup
    Log To Console    This is My Overriding Test Setup

My Overriding Test Teardown
    Log To Console    This is My Overriding Test Teardown
