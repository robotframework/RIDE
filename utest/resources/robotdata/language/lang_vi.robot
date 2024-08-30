# This is the preamble
Language: Vietnamese

# A blank line

*** Cài Đặt ***
Tài liệu hướng dẫn    This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
Tiền thiết lập bộ kịch bản kiểm thử    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Hậu thiết lập bộ kịch bản kiểm thử    My Suite Teardown    ${scalar}    @{LIST}
Tiền thiết lập kịch bản kiểm thử    My Test Setup
Hậu thiết lập kịch bản kiểm thử    My Overriding Test Teardown
Các nhãn kịch bản kiểm thử    new_tag    ride    regeression    # Comment on Tags
Dữ liệu tham chiếu    My Meta    data
Thư viện          seleniumlibrary    # Purposefully wrong case | |
Thư viện          Process    # This is a comment
Tài nguyên        en/full_en.resource
Thư viện          LibSpecLibrary
Thư viện          ${LIB NAME}
Thư viện          ArgLib    ${ARG}
Tài nguyên        ../resources/resource.resource
Tài nguyên        ../resources/resource2.robot
Tài nguyên        PathResource.robot
Tài nguyên        ../resources/resource.robot
Tài nguyên        ${RES_PATH}/another_resource.robot
Tài nguyên        ${RES_PATH}/more_resources/${RES NAME}
Tài nguyên        ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Biến số           ../resources/varz.py
Biến số           ../resources/dynamic_varz.py    ${ARG}
Biến số           en/full_en.yaml    # This is a comment
Biến số           en/full_en.json    # This is a comment
Biến số           en/full_en.py    # This is a comment
Biến số           ${RES_PATH}/more_varz.py
Thư viện          ${technology lib}    # defined in varz.py | |
Thư viện          ${operating system}    # defined in another_resource.robot | |

*** Các biến số ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Các chú thích ***
This is a comments block
Second line of comments
*** Các kịch bản kiểm thử ***
My Test
    [Tài liệu hướng dẫn]    This is _test_ *case* documentation
    [Các thẻ]    test 1
    [Tiền thiết lập]    My Overriding Test Setup
    Log    Nothing to see
    [Hậu thiết lập]    My Overriding Test Teardown

first test
    [Tài liệu hướng dẫn]    3-This is the documentation\n4-A continued line of documentation
    [Các thẻ]    first    second
    [Tiền thiết lập]    Log To Console    Test Setup
    [Thời gian chờ]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Vâng'
    ${second}=    Check Logic    'Tắt'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Hậu thiết lập]    Log To Console    Test Teardown

second test
    [Các thẻ]    first    second    # This is a comment
    [Tiền thiết lập]    Log To Console    Test Setup    # This is a comment
    [Mẫu]    First Keyword    # This is a comment
    [Thời gian chờ]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Hậu thiết lập]    Log To Console    Test Teardown    # This is a comment

third test
    Đã cho "Mr. Smith" is registered
    Và "cart" has objects
    Khi "Mr. Smith" clicks in checkout
    Thì the total is presented and awaits confirmation
    Nhưng it is shown the unavailable payment method

*** Các từ khóa ***
My Suite Teardown
    [Các đối số]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Tài liệu hướng dẫn]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Thời gian chờ]
    No Operation

First Keyword
    [Các đối số]    ${arg}=None    @{no_list}    # This is a comment
    [Tài liệu hướng dẫn]    5-This is the documentation\n\n7-A continued line of documentation
    [Các thẻ]    first    second    # This is a comment
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
