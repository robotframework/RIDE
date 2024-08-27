# This is the preamble
Language: Romanian

# A blank line

*** Setari ***
Documentatie      This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
Configurare De Suita    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Configurare De Intrerupere    My Suite Teardown    ${scalar}    @{LIST}
Setare De Test    My Test Setup
Inrerupere De Test    My Overriding Test Teardown
Taguri De Test    new_tag    ride    regeression    # Comment on Tags
Metadate          My Meta    data
Librarie          seleniumlibrary    # Purposefully wrong case | |
Librarie          Process    # This is a comment
Resursa           en/full_en.resource
Librarie          LibSpecLibrary
Librarie          ${LIB NAME}
Librarie          ArgLib    ${ARG}
Resursa           ../resources/resource.resource
Resursa           ../resources/resource2.robot
Resursa           PathResource.robot
Resursa           ../resources/resource.robot
Resursa           ${RES_PATH}/another_resource.robot
Resursa           ${RES_PATH}/more_resources/${RES NAME}
Resursa           ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Variabila         ../resources/varz.py
Variabila         ../resources/dynamic_varz.py    ${ARG}
Variabila         en/full_en.yaml    # This is a comment
Variabila         en/full_en.json    # This is a comment
Variabila         en/full_en.py    # This is a comment
Variabila         ${RES_PATH}/more_varz.py
Librarie          ${technology lib}    # defined in varz.py | |
Librarie          ${operating system}    # defined in another_resource.robot | |

*** Variabile ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Comentarii ***
This is a comments block
Second line of comments
*** Cazuri De Test ***
My Test
    [Documentatie]    This is _test_ *case* documentation
    [Etichete]    test 1
    [Setare]    My Overriding Test Setup
    Log    Nothing to see
    [Intrerupere]    My Overriding Test Teardown

first test
    [Documentatie]    3-This is the documentation\n4-A continued line of documentation
    [Etichete]    first    second
    [Setare]    Log To Console    Test Setup
    [Expirare]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Da'
    ${second}=    Check Logic    'Oprit'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Intrerupere]    Log To Console    Test Teardown

second test
    [Etichete]    first    second    # This is a comment
    [Setare]    Log To Console    Test Setup    # This is a comment
    [Sablon]    First Keyword    # This is a comment
    [Expirare]    60    # This is a comment
    No OperationNo Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Intrerupere]    Log To Console    Test Teardown    # This is a comment

third test
    Fie ca "Mr. Smith" is registered
    Si "cart" has objects
    Cand "Mr. Smith" clicks in checkout
    Atunci the total is presented and awaits confirmation
    Dar it is shown the unavailable payment method

*** Cuvinte Cheie ***
My Suite Teardown
    [Argumente]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Documentatie]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Expirare]
    No Operation

First Keyword
    [Argumente]    ${arg}=None    @{no_list}    # This is a comment
    [Documentatie]    5-This is the documentation\n\n7-A continued line of documentation
    [Etichete]    first    second    # This is a comment
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
