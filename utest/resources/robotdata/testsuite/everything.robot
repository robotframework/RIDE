*** Settings ***
Documentation     This test data file is used in *RobotIDE* _integration_ tests.
Suite Setup       My Suite Setup
Suite Teardown    My Suite Teardown    ${scalar}    @{LIST}
Test Setup        My Test Setup
Test Teardown     My Test Teardown
Force Tags        ride
Default Tags      regeression
Metadata          My Meta    data
Library           seleniumlibrary    # Purposefully wrong case | |
Library           TestLib
Library           LibSpecLibrary
Library           ${LIB NAME}
Library           ArgLib    ${ARG}
Resource          ../resources/resource.resource
Resource          PathResource.robot
Resource          resuja/resource.robot
Resource          spec_resource.html
Resource          ${RES_PATH}/another_resource.robot
Resource          ${RES_PATH}/more_resources/${RES NAME}
Resource          ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Variables         ../resources/varz.py
Variables         ../resources/dynamic_varz.py    ${ARG}
Variables         ${RES_PATH}/more_varz.py
Library           ${technology lib}    # defined in varz.py | |
Library           ${operating system}    # defined in another_resource.robot | |

*** Variables ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value

*** Test Cases ***
My Test
    [Documentation]    This is _test_ *case* documentation
    [Tags]    test 1
    [Setup]    My Overriding Test Setup
    Log    Nothing to see
    [Teardown]    My Overriding Test Teardown

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
