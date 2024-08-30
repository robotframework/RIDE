# This is the preamble
Language: Bulgarian

# A blank line

*** Настройки ***
Документация      This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
Първоначални настройки на комплекта    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Приключване на комплекта    My Suite Teardown    ${scalar}    @{LIST}
Първоначални настройки на тестове    My Test Setup
Приключване на тестове    My Overriding Test Teardown
Етикети за тестове    new_tag    ride    regeression    # Comment on Tags
Метаданни         My Meta    data
Библиотека        seleniumlibrary    # Purposefully wrong case | |
Библиотека        Process    # This is a comment
Ресурс            en/full_en.resource
Библиотека        LibSpecБиблиотека
Библиотека        ${LIB NAME}
Библиотека        ArgLib    ${ARG}
Ресурс            ../resources/resource.resource
Ресурс            ../resources/resource2.robot
Ресурс            PathResource.robot
Ресурс            ../resources/resource.robot
Ресурс            ${RES_PATH}/another_resource.robot
Ресурс            ${RES_PATH}/more_resources/${RES NAME}
Ресурс            ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Променлива        ../resources/varz.py
Променлива        ../resources/dynamic_varz.py    ${ARG}
Променлива        en/full_en.yaml    # This is a comment
Променлива        en/full_en.json    # This is a comment
Променлива        en/full_en.py    # This is a comment
Променлива        ${RES_PATH}/more_varz.py
Библиотека        ${technology lib}    # defined in varz.py | |
Библиотека        ${operating system}    # defined in another_resource.robot | |

*** Променливи ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Коментари ***
This is a comments block
Second line of comments
*** Тестови случаи ***
My Test
    [Документация]    This is _test_ *case* documentation
    [Етикети]    test 1
    [Първоначални настройки]    My Overriding Test Setup
    Log    Nothing to see
    [Приключване]    My Overriding Test Teardown

first test
    [Документация]    3-This is the documentation\n4-A continued line of documentation
    [Етикети]    first    second
    [Първоначални настройки]    Log To Console    Test Първоначални настройки
    [Таймаут]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Да'
    ${second}=    Check Logic    'Изключен'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Приключване]    Log To Console    Приключване на тестове

second test
    [Етикети]    first    second    # This is a comment
    [Първоначални настройки]    Log To Console    Test Първоначални настройки    # This is a comment
    [Шаблон]    First Keyword    # This is a comment
    [Таймаут]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Приключване]    Log To Console    Приключване на тестове    # This is a comment

third test
    В случай че "Mr. Smith" is registered
    И "cart" has objects
    Когато "Mr. Smith" clicks in checkout
    Тогава the total is presented and awaits confirmation
    Но it is shown the unavailable payment method

*** Ключови думи ***
My Приключване на комплекта
    [Аргументи]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Документация]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Таймаут]
    No Operation

First Keyword
    [Аргументи]    ${arg}=None    @{no_list}    # This is a comment
    [Документация]    5-This is the documentation\n\n7-A continued line of documentation
    [Етикети]    first    second    # This is a comment
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
