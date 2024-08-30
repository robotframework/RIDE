# This is the preamble
Language: French

# A blank line

*** Paramètres ***
Documentation     This test data file is used in *RobotIDE* _integration_ tests.
...               1-This is another line of the documentation
...               2-A continued line of documentation
Mise en place de suite    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Démontage de suite    My Suite Teardown    ${scalar}    @{LIST}
Mise en place de test    My Test Setup
Test Teardown     My Overriding Test Teardown
Étiquette de test    new_tag    ride    regeression    # Comment on Tags
Méta-donnée       My Meta    data
Bibliothèque      seleniumlibrary    # Purposefully wrong case | |
Bibliothèque      Process    # This is a comment
Ressource         en/full_en.resource
Bibliothèque      LibSpecLibrary
Bibliothèque      ${LIB NAME}
Bibliothèque      ArgLib    ${ARG}
Ressource         ../resources/resource.resource
Ressource         ../resources/resource2.robot
Ressource         PathResource.robot
Ressource         ../resources/resource.robot
Ressource         ${RES_PATH}/another_resource.robot
Ressource         ${RES_PATH}/more_resources/${RES NAME}
Ressource         ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Variable          ../resources/varz.py
Variable          ../resources/dynamic_varz.py    ${ARG}
Variable          en/full_en.yaml    # This is a comment
Variable          en/full_en.json    # This is a comment
Variable          en/full_en.py    # This is a comment
Variable          ${RES_PATH}/more_varz.py
Bibliothèque      ${technology lib}    # defined in varz.py | |
Bibliothèque      ${operating system}    # defined in another_resource.robot | |

*** Variables ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c
...               d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Commentaires ***
This is a comments block
Second line of comments
*** Unités de test ***
My Test
    [Documentation]    This is _test_ *case* documentation
    [Étiquette]    test 1
    [Mise en place]    My Overriding Test Setup
    Log    Nothing to see
    [Démontage]    My Overriding Test Teardown

first test
    [Documentation]    3-This is the documentation
    ...    4-A continued line of documentation
    [Étiquette]    first    second
    [Mise en place]    Log To Console    Test Setup
    [Délai d'attente]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Oui'
    ${second}=    Check Logic    'Désactivé'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Démontage]    Log To Console    Test Teardown

second test
    [Étiquette]    first    second    # This is a comment
    [Mise en place]    Log To Console    Test Setup    # This is a comment
    [Modèle]    First Keyword    # This is a comment
    [Délai d'attente]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Démontage]    Log To Console    Test Teardown    # This is a comment

third test
    Étant donné "Mr. Smith" is registered
    Et "cart" has objects
    Lorsque "Mr. Smith" clicks in checkout
    Alors the total is presented and awaits confirmation
    Mais it is shown the unavailable payment method

*** Mots-clés ***
My Suite Teardown
    [Arguments]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Documentation]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Délai d'attente]
    No Operation

First Keyword
    [Arguments]    ${arg}=None    @{no_list}    # This is a comment
    [Documentation]    5-This is the documentation
    ...
    ...    7-A continued line of documentation
    [Étiquette]    first    second    # This is a comment
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
