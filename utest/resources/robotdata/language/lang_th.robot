# This is the preamble
Language: Thai

# A blank line

*** การตั้งค่า ***
เอกสาร     This test data file is used in *RobotIDE* _integration_ tests.
...               1-This is another line of the documentation
...               2-A continued line of documentation
Suite Setup       Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Suite Teardown    My Suite Teardown    ${scalar}    @{LIST}
Test Setup        My Test Setup
Test Teardown     My Overriding Test Teardown
กลุ่มของการทดสอบ         new_tag    ride    regeression    # Comment on Tags
รายละเอียดเพิ่มเติม          My Meta    data
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

*** กำหนดตัวแปร ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** คำอธิบาย ***
This is a comments block
Second line of comments
*** การทดสอบ ***
My Test
    [เอกสาร]    This is _test_ *case* documentation
    [Tags]    test 1
    [กำหนดค่าเริ่มต้น]    My Overriding Test Setup
    Log    Nothing to see
    [คืนค่า]    My Overriding Test Teardown

first test
    [เอกสาร]    3-This is the documentation
    ...    4-A continued line of documentation
    [Tags]    first    second
    [กำหนดค่าเริ่มต้น]    Log To Console    Test Setup
    [หมดเวลา]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Yes'
    ${second}=    Check Logic    'Off'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [คืนค่า]    Log To Console    Test Teardown

second test
    [Tags]    first    second    # This is a comment
    [กำหนดค่าเริ่มต้น]    Log To Console    Test Setup    # This is a comment
    [Template]    First Keyword    # This is a comment
    [หมดเวลา]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [คืนค่า]    Log To Console    Test Teardown    # This is a comment

third test
    กำหนดให้ "Mr. Smith" is registered
    และ "cart" has objects
    เมื่อ "Mr. Smith" clicks in checkout
    ดังนั้น the total is presented and awaits confirmation
    แต่ it is shown the unavailable payment method

*** คำสั่งเพิ่มเติม ***
My Suite Teardown
    [ค่าที่ส่งเข้ามา]    ${scalar arg}    ${default arg}=default    @{list arg}
    [เอกสาร]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [หมดเวลา]
    No Operation

First Keyword
    [ค่าที่ส่งเข้ามา]    ${arg}=None    @{no_list}    # This is a comment
    [เอกสาร]    5-This is the documentation
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
