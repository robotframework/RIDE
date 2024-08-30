# This is the preamble
Language: Swedish

# A blank line

*** Inställningar ***
Dokumentation     This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
Svit konfigurering    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Svit nedrivning    My Suite Teardown    ${scalar}    @{LIST}
Test konfigurering    My Test Setup
Test nedrivning    My Overriding Test Teardown
Test taggar       new_tag    ride    regeression    # Comment on Tags
Metadata          My Meta    data
Bibliotek         seleniumlibrary    # Purposefully wrong case | |
Bibliotek         Process    # This is a comment
Resurs            en/full_en.resource
Bibliotek         LibSpecLibrary
Bibliotek         ${LIB NAME}
Bibliotek         ArgLib    ${ARG}
Resurs            ../resources/resource.resource
Resurs            ../resources/resource2.robot
Resurs            PathResource.robot
Resurs            ../resources/resource.robot
Resurs            ${RES_PATH}/another_resource.robot
Resurs            ${RES_PATH}/more_resources/${RES NAME}
Resurs            ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Variabel          ../resources/varz.py
Variabel          ../resources/dynamic_varz.py    ${ARG}
Variabel          en/full_en.yaml    # This is a comment
Variabel          en/full_en.json    # This is a comment
Variabel          en/full_en.py    # This is a comment
Variabel          ${RES_PATH}/more_varz.py
Bibliotek         ${technology lib}    # defined in varz.py | |
Bibliotek         ${operating system}    # defined in another_resource.robot | |

*** Variabler ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Kommentarer ***
This is a comments block
Second line of comments
*** Testfall ***
My Test
    [Dokumentation]    This is _test_ *case* documentation
    [Taggar]    test 1
    [Konfigurering]    My Overriding Test Setup
    Log    Nothing to see
    [Nedrivning]    My Overriding Test Teardown

first test
    [Dokumentation]    3-This is the documentation\n4-A continued line of documentation
    [Taggar]    first    second
    [Konfigurering]    Log To Console    Test Setup
    [Timeout]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Ja'
    ${second}=    Check Logic    'Av'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Nedrivning]    Log To Console    Test Teardown

second test
    [Taggar]    first    second    # This is a comment
    [Konfigurering]    Log To Console    Test Setup    # This is a comment
    [Mall]    First Keyword    # This is a comment
    [Timeout]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Nedrivning]    Log To Console    Test Teardown    # This is a comment

third test
    Givet "Mr. Smith" is registered
    Och "cart" has objects
    När "Mr. Smith" clicks in checkout
    Då the total is presented and awaits confirmation
    Men it is shown the unavailable payment method

*** Nyckelord ***
My Suite Teardown
    [Argument]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Dokumentation]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Timeout]
    No Operation

First Keyword
    [Argument]    ${arg}=None    @{no_list}    # This is a comment
    [Dokumentation]    5-This is the documentation\n\n7-A continued line of documentation
    [Taggar]    first    second    # This is a comment
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
