# This is the preamble
Language: Italian

# A blank line

*** Impostazioni ***
Documentazione     This test data file is used in *RobotIDE* _integration_ tests.
...               1-This is another line of the documentation
...               2-A continued line of documentation
Configurazione Suite       Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Distruzione Suite    My Suite Teardown    ${scalar}    @{LIST}
Configurazione Test        My Test Setup
Distruzione Test     My Overriding Test Teardown
Tag Del Test         new_tag    ride    regeression    # Comment on Tags
Metadati          My Meta    data
Libreria           seleniumlibrary    # Purposefully wrong case | |
Libreria           Process    # This is a comment
Risorsa          en/full_en.resource
Libreria           LibSpecLibrary
Libreria           ${LIB NAME}
Libreria           ArgLib    ${ARG}
Risorsa          ../resources/resource.resource
Risorsa          ../resources/resource2.robot
Risorsa          PathResource.robot
Risorsa          ../resources/resource.robot
Risorsa          ${RES_PATH}/another_resource.robot
Risorsa          ${RES_PATH}/more_resources/${RES NAME}
Risorsa          ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Variabile         ../resources/varz.py
Variabile         ../resources/dynamic_varz.py    ${ARG}
Variabile         en/full_en.yaml    # This is a comment
Variabile         en/full_en.json    # This is a comment
Variabile         en/full_en.py    # This is a comment
Variabile         ${RES_PATH}/more_varz.py
Libreria           ${technology lib}    # defined in varz.py | |
Libreria           ${operating system}    # defined in another_resource.robot | |

*** Variabili ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c
...               d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Commenti ***
This is a comments block
Second line of comments
*** Casi Di Test ***
My Test
    [Documentazione]    This is _test_ *case* documentation
    [Tag]    test 1
    [Configurazione]    My Overriding Test Setup
    Log    Nothing to see
    [Distruzione]    My Overriding Test Teardown

first test
    [Documentazione]    3-This is the documentation
    ...    4-A continued line of documentation
    [Tag]    first    second
    [Configurazione]    Log To Console    Test Setup
    [Timeout]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Sì'
    ${second}=    Check Logic    'Off'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Distruzione]    Log To Console    Test Teardown

second test
    [Tag]    first    second    # This is a comment
    [Configurazione]    Log To Console    Test Setup    # This is a comment
    [Template]    First Keyword    # This is a comment
    [Timeout]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Distruzione]    Log To Console    Test Teardown    # This is a comment

third test
    Dato "Mr. Smith" is registered
    E "cart" has objects
    Quando "Mr. Smith" clicks in checkout
    Allora the total is presented and awaits confirmation
    Ma it is shown the unavailable payment method

*** Parole Chiave ***
My Suite Teardown
    [Parametri]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Documentazione]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Timeout]
    No Operation

First Keyword
    [Parametri]    ${arg}=None    @{no_list}    # This is a comment
    [Documentazione]    5-This is the documentation
    ...
    ...    7-A continued line of documentation
    [Tag]    first    second    # This is a comment
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
