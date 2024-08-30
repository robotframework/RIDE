# This is the preamble
Language: Korean

# A blank line

*** 설정 ***
문서                This test data file is used in *RobotIDE* _integration_ test
...               1-This is another line of the documentation
...               2-A continued line of documentation
스위트 설정            Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
스위트 중단            My Suite Teardown    ${scalar}    @{LIST}
테스트 설정            My Test Setup
테스트 태그            new_tag    ride    regeression    # Comment on Tags
메타데이터             My Meta    data
라이브러리             seleniumlibrary    # Purposefully wrong case | |
라이브러리             Process    # This is a comment
자료                en/full_en.resource
라이브러리             LibSpecLibrary
라이브러리             ${LIB NAME}
라이브러리             ArgLib    ${ARG}
자료                ../resources/resource.resource
자료                ../resources/resource2.robot
자료                PathResource.robot
자료                ../resources/resource.robot
자료                ${RES_PATH}/another_resource.robot
자료                ${RES_PATH}/more_resources/${RES NAME}
자료                ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
변수                ../resources/varz.py
변수                ../resources/dynamic_varz.py    ${ARG}
변수                en/full_en.yaml    # This is a comment
변수                en/full_en.json    # This is a comment
변수                en/full_en.py    # This is a comment
변수                ${RES_PATH}/more_varz.py
라이브러리             ${technology lib}    # defined in varz.py | |
라이브러리             ${operating system}    # defined in another_resource.robot | |

*** 변수 ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c
...               d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** 의견 ***
This is a comments block
Second line of comments
*** 테스트 사례 ***
My Test
    [문서]    This is _test_ *case* documentation
    [설정]    My Overriding Test Setup
    Log    Nothing to see
    [중단]    My Overriding Test Teardown

first test
    [문서]    3-This is the documentation
    ...    4-A continued line of documentation
    [설정]    Log To Console    Test Setup
    [시간 초과]    60
    First Keyword    nonsense
    ${first}=    Check Logic    '有効'
    ${second}=    Check Logic    'いいえ'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [중단]    Log To Console    Test Teardown

second test
    [설정]    Log To Console    Test Setup    # This is a comment
    [시간 초과]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [중단]    Log To Console    Test Teardown    # This is a comment

third test
    주어진 "Mr. Smith" is registered
    그리고 "cart" has objects
    때 "Mr. Smith" clicks in checkout
    보다 the total is presented and awaits confirmation
    하지만 it is shown the unavailable payment method

*** 키워드 ***
My Suite Teardown
    [주장]    ${scalar arg}    ${default arg}=default    @{list arg}
    [문서]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [시간 초과]
    No Operation

First Keyword
    [주장]    ${arg}=None    @{no_list}    # This is a comment
    [문서]    5-This is the documentation
    ...
    ...    7-A continued line of documentation
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
