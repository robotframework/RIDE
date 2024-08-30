# This is the preamble
Language: Dutch

# A blank line

*** Instellingen ***
Documentatie      This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
Suite Preconditie    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Suite Postconditie    My Suite Teardown    ${scalar}    @{LIST}
Test Preconditie    My Test Setup
Test Postconditie    My Overriding Test Teardown
Test Labels       new_tag    ride    regeression    # Comment on Tags
Metadata          My Meta    data
Bibliotheek       seleniumlibrary    # Purposefully wrong case | |
Bibliotheek       Process    # This is a comment
Resource          en/full_en.resource
Bibliotheek       LibSpecLibrary
Bibliotheek       ${LIB NAME}
Bibliotheek       ArgLib    ${ARG}
Resource          ../resources/resource.resource
Resource          ../resources/resource2.robot
Resource          PathResource.robot
Resource          ../resources/resource.robot
Resource          ${RES_PATH}/another_resource.robot
Resource          ${RES_PATH}/more_resources/${RES NAME}
Resource          ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Variabele         ../resources/varz.py
Variabele         ../resources/dynamic_varz.py    ${ARG}
Variabele         en/full_en.yaml    # This is a comment
Variabele         en/full_en.json    # This is a comment
Variabele         en/full_en.py    # This is a comment
Variabele         ${RES_PATH}/more_varz.py
Bibliotheek       ${technology lib}    # defined in varz.py | |
Bibliotheek       ${operating system}    # defined in another_resource.robot | |

*** Variabelen ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Opmerkingen ***
This is a comments block
Second line of comments
*** Testgevallen ***
My Test
    [Documentatie]    This is _test_ *case* documentation
    [Labels]    test 1
    [Preconditie]    My Overriding Test Setup
    Log    Nothing to see
    [Postconditie]    My Overriding Test Teardown

first test
    [Documentatie]    3-This is the documentation\n4-A continued line of documentation
    [Labels]    first    second
    [Preconditie]    Log To Console    Test Setup
    [Time-out]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Ja'
    ${second}=    Check Logic    'Uit'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Postconditie]    Log To Console    Test Teardown

second test
    [Labels]    first    second    # This is a comment
    [Preconditie]    Log To Console    Test Setup    # This is a comment
    [Sjabloon]    First Keyword    # This is a comment
    [Time-out]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Postconditie]    Log To Console    Test Teardown    # This is a comment

third test
    Stel "Mr. Smith" is registered
    En "cart" has objects
    Als "Mr. Smith" clicks in checkout
    Dan the total is presented and awaits confirmation
    Maar it is shown the unavailable payment method

*** Sleutelwoorden ***
My Suite Teardown
    [Parameters]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Documentatie]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Time-out]
    No Operation

First Keyword
    [Parameters]    ${arg}=None    @{no_list}    # This is a comment
    [Documentatie]    5-This is the documentation\n\n7-A continued line of documentation
    [Labels]    first    second    # This is a comment
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
