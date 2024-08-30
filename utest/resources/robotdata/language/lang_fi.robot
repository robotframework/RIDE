# This is the preamble
Language: Finnish

# A blank line

*** Asetukset ***
Dokumentaatio     This test data file is used in *RobotIDE* _integration_ tests.
...               1-This is another line of the documentation
...               2-A continued line of documentation
Setin Alustus     Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Setin Alasajo     My Suite Teardown    ${scalar}    @{LIST}
Testin Alustus    My Test Setup
Testin Alasajo    My Overriding Test Teardown
Testin Tagit      new_tag    ride    regeression    # Comment on Tags
Metatiedot        My Meta    data
Kirjasto          seleniumlibrary    # Purposefully wrong case | |
Kirjasto          Process    # This is a comment
Resurssi          en/full_en.resource
Kirjasto          LibSpecLibrary
Kirjasto          ${LIB NAME}
Kirjasto          ArgLib    ${ARG}
Resurssi          ../resources/resource.resource
Resurssi          ../resources/resource2.robot
Resurssi          PathResource.robot
Resurssi          ../resources/resource.robot
Resurssi          ${RES_PATH}/another_resource.robot
Resurssi          ${RES_PATH}/more_resources/${RES NAME}
Resurssi          ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Muuttujat         ../resources/varz.py
Muuttujat         ../resources/dynamic_varz.py    ${ARG}
Muuttujat         en/full_en.yaml    # This is a comment
Muuttujat         en/full_en.json    # This is a comment
Muuttujat         en/full_en.py    # This is a comment
Muuttujat         ${RES_PATH}/more_varz.py
Kirjasto          ${technology lib}    # defined in varz.py | |
Kirjasto          ${operating system}    # defined in another_resource.robot | |

*** Muuttujat ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c
...               d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Kommentit ***
This is a comments block
Second line of comments
*** Testit ***
My Test
    [Dokumentaatio]    This is _test_ *case* documentation
    [Tagit]    test 1
    [Alustus]    My Overriding Test Setup
    Log    Nothing to see
    [Alasajo]    My Overriding Test Teardown

first test
    [Dokumentaatio]    3-This is the documentation
    ...    4-A continued line of documentation
    [Tagit]    first    second
    [Alustus]    Log To Console    Test Setup
    [Aikaraja]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Kyllä'
    ${second}=    Check Logic    'Pois'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Alasajo]    Log To Console    Test Teardown

second test
    [Tagit]    first    second    # This is a comment
    [Alustus]    Log To Console    Test Setup    # This is a comment
    [Malli]    First Keyword    # This is a comment
    [Aikaraja]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Alasajo]    Log To Console    Test Teardown    # This is a comment

third test
    Oletetaan "Mr. Smith" is registered
    Ja "cart" has objects
    Kun "Mr. Smith" clicks in checkout
    Niin the total is presented and awaits confirmation
    Mutta it is shown the unavailable payment method

*** Avainsanat ***
My Suite Teardown
    [Argumentit]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Dokumentaatio]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Aikaraja]
    No Operation

First Keyword
    [Argumentit]    ${arg}=None    @{no_list}    # This is a comment
    [Dokumentaatio]    5-This is the documentation
    ...
    ...    7-A continued line of documentation
    [Tagit]    first    second    # This is a comment
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
