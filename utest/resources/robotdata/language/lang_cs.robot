# This is the preamble
Language: Czech

# A blank line

*** Nastavení ***
Dokumentace       This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
Příprava sady     Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Ukončení sady     My Suite Teardown    ${scalar}    @{LIST}
Příprava testu    My Test Setup
Ukončení testu    My Overriding Test Teardown
Štítky testů      new_tag    ride    regeression    # Comment on Tags
Metadata          My Meta    data
Knihovna          seleniumlibrary    # Purposefully wrong case | |
Knihovna          Process    # This is a comment
Zdroj             en/full_en.resource
Knihovna          LibSpecLibrary
Knihovna          ${LIB NAME}
Knihovna          ArgLib    ${ARG}
Zdroj             ../resources/resource.resource
Zdroj             ../resources/resource2.robot
Zdroj             PathResource.robot
Zdroj             ../resources/resource.robot
Zdroj             ${RES_PATH}/another_resource.robot
Zdroj             ${RES_PATH}/more_resources/${RES NAME}
Zdroj             ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Proměnná          ../resources/varz.py
Proměnná          ../resources/dynamic_varz.py    ${ARG}
Proměnná          en/full_en.yaml    # This is a comment
Proměnná          en/full_en.json    # This is a comment
Proměnná          en/full_en.py    # This is a comment
Proměnná          ${RES_PATH}/more_varz.py
Knihovna          ${technology lib}    # defined in varz.py | |
Knihovna          ${operating system}    # defined in another_resource.robot | |

*** Proměnné ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Komentáře ***
This is a comments block
Second line of comments
*** Testovací případy ***
My Test
    [Dokumentace]    This is _test_ *case* documentation
    [Štítky]    test 1
    [Příprava]    My Overriding Test Setup
    Log    Nothing to see
    [Ukončení]    My Overriding Test Teardown

first test
    [Dokumentace]    3-This is the documentation\n4-A continued line of documentation
    [Štítky]    first    second
    [Příprava]    Log To Console    Test Setup
    [Časový limit]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Ano'
    ${second}=    Check Logic    'Vypnuto'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Ukončení]    Log To Console    Test Teardown

second test
    [Štítky]    first    second    # This is a comment
    [Příprava]    Log To Console    Test Setup    # This is a comment
    [Šablona]    First Keyword    # This is a comment
    [Časový limit]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Ukončení]    Log To Console    Test Teardown    # This is a comment

third test
    Pokud "Mr. Smith" is registered
    A "cart" has objects
    Když "Mr. Smith" clicks in checkout
    Pak the total is presented and awaits confirmation
    Ale it is shown the unavailable payment method

*** Klíčová slova ***
My Suite Teardown
    [Argumenty]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Dokumentace]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Časový limit]
    No Operation

First Keyword
    [Argumenty]    ${arg}=None    @{no_list}    # This is a comment
    [Dokumentace]    5-This is the documentation\n\n7-A continued line of documentation
    [Štítky]    first    second    # This is a comment
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
