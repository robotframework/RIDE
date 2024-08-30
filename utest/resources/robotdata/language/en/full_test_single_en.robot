# This is the preamble
Language: English

# A blank line

*** Settings ***
Documentation     1-This is the documentation
...               2-A continued line of documentation
Suite Setup       Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
Suite Teardown    Log To Console    Suite Teardown
Metadata          Name    Value    # This is a comment
Library           Process    # This is a comment
Variables         full_en.yaml    # This is a comment
Variables         full_en.json    # This is a comment
Variables         full_en.py    # This is a comment
Resource          full_en.resource

*** Variables ***
${myvar}          123    # This is a comment

*** Comments ***
This is a comments block
Second line of comments
*** Test Cases ***
first test
    [Documentation]    3-This is the documentation
    ...    4-A continued line of documentation
    [Tags]    first    second
    [Setup]    Log To Console    Test Setup
    [Timeout]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Yes'
    ${second}=    Check Logic    'Off'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Teardown]    Log To Console    Test Teardown

second test
    [Tags]    first    second    # This is a comment
    [Setup]    Log To Console    Test Setup    # This is a comment
    [Template]    First Keyword    # This is a comment
    [Timeout]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Teardown]    Log To Console    Test Teardown    # This is a comment

third test
    Given "Mr. Smith" is registered
    And "cart" has objects
    When "Mr. Smith" clicks in checkout
    Then the total is presented and awaits confirmation
    But it is shown the unavailable payment method

*** Keywords ***
First Keyword
    [Arguments]    ${arg}=None    @{no_list}    # This is a comment
    [Documentation]    5-This is the documentation
    ...
    ...    7-A continued line of documentation
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
