# This is the preamble
Language: English

# A blank line

*** Settings ***
Documentation     This test data file is used in *RobotIDE* _integration_ tests.
...               1-This is another line of the documentation
...               2-A continued line of documentation
Suite Setup       Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Suite Teardown    My Suite Teardown    ${scalar}    @{LIST}
Test Setup        My Test Setup
Test Teardown     My Overriding Test Teardown
Test Tags         new_tag    ride    regeression    # Comment on Tags
Metadata          My Meta    data
Library           seleniumlibrary    # Purposefully wrong case | |
Library           Process    # This is a comment
Resource          en/full_en.resource
Library           LibSpecLibrary
Library           ${LIB NAME}
Library           ArgLib    ${ARG}
Resource          ../resources/resource.resource
Resource          ../resources/resource2.robot
Resource          PathResource.robot
Resource          ../resources/resource.robot
Resource          ${RES_PATH}/another_resource.robot
Resource          ${RES_PATH}/more_resources/${RES NAME}
Resource          ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Variables         ../resources/varz.py
Variables         ../resources/dynamic_varz.py    ${ARG}
Variables         en/full_en.yaml    # This is a comment
Variables         en/full_en.json    # This is a comment
Variables         en/full_en.py    # This is a comment
Variables         ${RES_PATH}/more_varz.py
Library           ${technology lib}    # defined in varz.py | |
Library           ${operating system}    # defined in another_resource.robot | |

*** Variables ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c
...               d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Comments ***
This is a comments block
Second line of comments
*** Test Cases ***
My Test
    [Documentation]    This is _test_ *case* documentation
    [Tags]    test 1
    [Setup]    My Overriding Test Setup
    Log    Nothing to see
    [Teardown]    My Overriding Test Teardown

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
My Suite Teardown
    [Arguments]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Documentation]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Timeout]
    No Operation

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
