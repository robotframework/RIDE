# This is the preamble
Language: Chinese Simplified

# A blank line

*** 设置 ***
说明                This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
用例集启程             Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
用例集终程             My Suite Teardown    ${scalar}    @{LIST}
用例启程              My Test Setup
用例终程              My Overriding Test Teardown
用例标签              new_tag    ride    regeression    # Comment on Tags
元数据               My Meta    data
程序库               seleniumlibrary    # Purposefully wrong case | |
程序库               Process    # This is a comment
资源文件              en/full_en.resource
程序库               LibSpecLibrary
程序库               ${LIB NAME}
程序库               ArgLib    ${ARG}
资源文件              ../resources/resource.resource
资源文件              ../resources/resource2.robot
资源文件              PathResource.robot
资源文件              ../resources/resource.robot
资源文件              ${RES_PATH}/another_resource.robot
资源文件              ${RES_PATH}/more_resources/${RES NAME}
资源文件              ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
变量文件              ../resources/varz.py
变量文件              ../resources/dynamic_varz.py    ${ARG}
变量文件              en/full_en.yaml    # This is a comment
变量文件              en/full_en.json    # This is a comment
变量文件              en/full_en.py    # This is a comment
变量文件              ${RES_PATH}/more_varz.py
程序库               ${technology lib}    # defined in varz.py | |
程序库               ${operating system}    # defined in another_resource.robot | |

*** 变量 ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** 备注 ***
This is a comments block
Second line of comments
*** 用例 ***
My Test
    [说明]    This is _test_ *case* documentation
    [标签]    test 1
    [启程]    My Overriding Test Setup
    Log    Nothing to see
    [终程]    My Overriding Test Teardown

first test
    [说明]    3-This is the documentation\n4-A continued line of documentation
    [标签]    first    second
    [启程]    Log To Console    Test Setup
    [超时]    60
    First Keyword    nonsense
    ${first}=    Check Logic    '是'
    ${second}=    Check Logic    '关'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [终程]    Log To Console    Test Teardown

second test
    [标签]    first    second    # This is a comment
    [启程]    Log To Console    Test Setup    # This is a comment
    [模板]    First Keyword    # This is a comment
    [超时]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [终程]    Log To Console    Test Teardown    # This is a comment

third test
    假定 "Mr. Smith" is registered
    并且 "cart" has objects
    当 "Mr. Smith" clicks in checkout
    那么 the total is presented and awaits confirmation
    但是 it is shown the unavailable payment method

*** 关键字 ***
My Suite Teardown
    [参数]    ${scalar arg}    ${default arg}=default    @{list arg}
    [说明]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [超时]
    No Operation

First Keyword
    [参数]    ${arg}=None    @{no_list}    # This is a comment
    [说明]    5-This is the documentation\n\n7-A continued line of documentation
    [标签]    first    second    # This is a comment
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
