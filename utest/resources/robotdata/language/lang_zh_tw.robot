# This is the preamble
Language: Chinese Traditional

# A blank line

*** 設置 ***
說明                This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
測試套啟程             Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
測試套終程             My Suite Teardown    ${scalar}    @{LIST}
測試啟程              My Test Setup
測試終程              My Overriding Test Teardown
測試標籤              new_tag    ride    regeression    # Comment on Tags
元數據               My Meta    data
函式庫               seleniumlibrary    # Purposefully wrong case | |
函式庫               Process    # This is a comment
資源文件              en/full_en.resource
函式庫               LibSpecLibrary
函式庫               ${LIB NAME}
函式庫               ArgLib    ${ARG}
資源文件              ../resources/resource.resource
資源文件              ../resources/resource2.robot
資源文件              PathResource.robot
資源文件              ../resources/resource.robot
資源文件              ${RES_PATH}/another_resource.robot
資源文件              ${RES_PATH}/more_resources/${RES NAME}
資源文件              ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
變量文件              ../resources/varz.py
變量文件              ../resources/dynamic_varz.py    ${ARG}
變量文件              en/full_en.yaml    # This is a comment
變量文件              en/full_en.json    # This is a comment
變量文件              en/full_en.py    # This is a comment
變量文件              ${RES_PATH}/more_varz.py
函式庫               ${technology lib}    # defined in varz.py | |
函式庫               ${operating system}    # defined in another_resource.robot | |

*** 變量 ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** 備註 ***
This is a comments block
Second line of comments
*** 案例 ***
My Test
    [說明]    This is _test_ *case* documentation
    [標籤]    test 1
    [啟程]    My Overriding Test Setup
    Log    Nothing to see
    [終程]    My Overriding Test Teardown

first test
    [說明]    3-This is the documentation\n4-A continued line of documentation
    [標籤]    first    second
    [啟程]    Log To Console    Test Setup
    [逾時]    60
    First Keyword    nonsense
    ${first}=    Check Logic    '是'
    ${second}=    Check Logic    '關'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [終程]    Log To Console    Test Teardown

second test
    [標籤]    first    second    # This is a comment
    [啟程]    Log To Console    Test Setup    # This is a comment
    [模板]    First Keyword    # This is a comment
    [逾時]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [終程]    Log To Console    Test Teardown    # This is a comment

third test
    假定 "Mr. Smith" is registered
    並且 "cart" has objects
    當 "Mr. Smith" clicks in checkout
    那麼 the total is presented and awaits confirmation
    但是 it is shown the unavailable payment method

*** 關鍵字 ***
My Suite Teardown
    [参数]    ${scalar arg}    ${default arg}=default    @{list arg}
    [說明]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [逾時]
    No Operation

First Keyword
    [参数]    ${arg}=None    @{no_list}    # This is a comment
    [說明]    5-This is the documentation\n\n7-A continued line of documentation
    [標籤]    first    second    # This is a comment
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
