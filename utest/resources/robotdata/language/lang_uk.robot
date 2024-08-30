# This is the preamble
Language: Ukrainian

# A blank line

*** Налаштування ***
Документація     This test data file is used in *RobotIDE* _integration_ tests.
...               1-This is another line of the documentation
...               2-A continued line of documentation
Suite Setup       Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Suite Teardown    My Suite Teardown    ${scalar}    @{LIST}
Test Setup        My Test Setup
Test Teardown     My Overriding Test Teardown
Тестові теги         new_tag    ride    regeression    # Comment on Tags
Метадані          My Meta    data
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

*** Змінні ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Коментарів ***
This is a comments block
Second line of comments
*** Тест-кейси ***
My Test
    [Документація]    This is _test_ *case* documentation
    [Tags]    test 1
    [Встановлення]    My Overriding Test Setup
    Log    Nothing to see
    [Cпростовувати пункт за пунктом]    My Overriding Test Teardown

first test
    [Документація]    3-This is the documentation
    ...    4-A continued line of documentation
    [Tags]    first    second
    [Встановлення]    Log To Console    Test Setup
    [Час вийшов]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Yes'
    ${second}=    Check Logic    'Off'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Cпростовувати пункт за пунктом]    Log To Console    Test Teardown

second test
    [Tags]    first    second    # This is a comment
    [Встановлення]    Log To Console    Test Setup    # This is a comment
    [Template]    First Keyword    # This is a comment
    [Час вийшов]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Cпростовувати пункт за пунктом]    Log To Console    Test Teardown    # This is a comment

third test
    Дано "Mr. Smith" is registered
    Та "cart" has objects
    Коли "Mr. Smith" clicks in checkout
    Тоді the total is presented and awaits confirmation
    Але it is shown the unavailable payment method

*** Ключових слова ***
My Suite Teardown
    [Аргументи]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Документація]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Час вийшов]
    No Operation

First Keyword
    [Аргументи]    ${arg}=None    @{no_list}    # This is a comment
    [Документація]    5-This is the documentation
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
