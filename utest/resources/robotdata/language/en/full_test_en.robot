# This is the preamble
Language: English

# A blank line

*** Settings ***
Library    Process    # This is a comment
Resource      full_en.resource    # This is a comment
Variables      full_en.yaml    # This is a comment
Variables      full_en.json    # This is a comment
Variables      full_en.py    # This is a comment

Documentation    This is the documentation
...    A continued line of documentation

Metadata    Name    Value    # This is a comment

Suite Setup           Log To Console    Suite Setup
Suite Teardown        Log To Console    Suite Teardown

*** Variables ***
${myvar}    123    # This is a comment

*** Comments ***
This is a comments block
Second line of comments

*** Test Cases ***
first test
    [Documentation]    This is the documentation
    ...    A continued line of documentation
    [Setup]    Log To Console    Test Setup
    [Teardown]    Log To Console    Test Teardown
    [Timeout]    60
    [Tags]    first    second
    First Keyword
    ${first}=    Check Logic    'Yes'
    ${second}=    Check Logic    'Off'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}

second test
    [Template]    First Keyword    # This is a comment
    [Setup]    Log To Console    Test Setup    # This is a comment
    [Teardown]    Log To Console    Test Teardown    # This is a comment
    [Timeout]    60    # This is a comment
    [Tags]    first    second    # This is a comment
    No Operation
    First Keyword
    Log To Console Test executed with success

third test
    Given "Mr. Smith" is registered
    And "cart" has objects
    When "Mr. Smith" clicks in checkout
    Then the total is presented and awaits confirmation
    But it is shown the unavailable payment method

*** Keywords ***
First Keyword
    [Documentation]    This is the documentation
    ...    A continued line of documentation
    [Arguments]    ${arg}=None    # This is a comment
    [Tags]    first    second    # This is a comment
    Log To Console    This is the first keyword

${user} is registered
    No Operation

${cart} has objects
    No Operation

${user} clicks in checkout
    No Operation

the total is presented and awaits confirmation
    No Operation

it is shown the unavailable payment method
    No Operation

