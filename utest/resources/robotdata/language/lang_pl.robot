# This is the preamble
Language: Polish

# A blank line

*** Ustawienia ***
Dokumentacja      This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
Inicjalizacja Zestawu    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Ukończenie Zestawu    My Suite Teardown    ${scalar}    @{LIST}
Inicjalizacja Testu    My Test Setup
Ukończenie Testu    My Overriding Test Teardown
Znaczniki Testu    new_tag    ride    regeression    # Comment on Tags
Metadane          My Meta    data
Biblioteka        seleniumlibrary    # Purposefully wrong case | |
Biblioteka        Process    # This is a comment
Zasób             en/full_en.resource
Biblioteka        LibSpecLibrary
Biblioteka        ${LIB NAME}
Biblioteka        ArgLib    ${ARG}
Zasób             ../resources/resource.resource
Zasób             ../resources/resource2.robot
Zasób             PathResource.robot
Zasób             ../resources/resource.robot
Zasób             ${RES_PATH}/another_resource.robot
Zasób             ${RES_PATH}/more_resources/${RES NAME}
Zasób             ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Zmienne           ../resources/varz.py
Zmienne           ../resources/dynamic_varz.py    ${ARG}
Zmienne           en/full_en.yaml    # This is a comment
Zmienne           en/full_en.json    # This is a comment
Zmienne           en/full_en.py    # This is a comment
Zmienne           ${RES_PATH}/more_varz.py
Biblioteka        ${technology lib}    # defined in varz.py | |
Biblioteka        ${operating system}    # defined in another_resource.robot | |

*** Zmienne ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Komentarze ***
This is a comments block
Second line of comments
*** Przypadki Testowe ***
My Test
    [Dokumentacja]    This is _test_ *case* documentation
    [Znaczniki]    test 1
    [Inicjalizacja]    My Overriding Test Setup
    Log    Nothing to see
    [Ukończenie]    My Overriding Test Teardown

first test
    [Dokumentacja]    3-This is the documentation\n4-A continued line of documentation
    [Znaczniki]    first    second
    [Inicjalizacja]    Log To Console    Test Setup
    [Limit Czasowy]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Tak'
    ${second}=    Check Logic    'Wyłączone'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Ukończenie]    Log To Console    Test Teardown

second test
    [Znaczniki]    first    second    # This is a comment
    [Inicjalizacja]    Log To Console    Test Setup    # This is a comment
    [Szablon]    First Keyword    # This is a comment
    [Limit Czasowy]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Ukończenie]    Log To Console    Test Teardown    # This is a comment

third test
    Zakładając "Mr. Smith" is registered
    Oraz "cart" has objects
    Jeżeli "Mr. Smith" clicks in checkout
    Wtedy the total is presented and awaits confirmation
    Ale it is shown the unavailable payment method

*** Słowa Kluczowe ***
My Suite Teardown
    [Argumenty]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Dokumentacja]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Limit Czasowy]
    No Operation

First Keyword
    [Argumenty]    ${arg}=None    @{no_list}    # This is a comment
    [Dokumentacja]    5-This is the documentation\n\n7-A continued line of documentation
    [Znaczniki]    first    second    # This is a comment
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
