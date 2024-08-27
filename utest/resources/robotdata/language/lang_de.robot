# This is the preamble
Language: German

# A blank line

*** Einstellungen ***
Dokumentation     This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
Suitevorbereitung    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Suitenachbereitung    My Suite Teardown    ${scalar}    @{LIST}
Testvorbereitung    My Test Setup
Testnachbereitung    My Overriding Test Teardown
Testmarker        new_tag    ride    regeression    # Comment on Tags
Metadaten         My Meta    data
Bibliothek        seleniumlibrary    # Purposefully wrong case | |
Bibliothek        Process    # This is a comment
Ressource         en/full_en.resource
Bibliothek        LibSpecLibrary
Bibliothek        ${LIB NAME}
Bibliothek        ArgLib    ${ARG}
Ressource         ../resources/resource.resource
Ressource         ../resources/resource2.robot
Ressource         PathResource.robot
Ressource         ../resources/resource.robot
Ressource         ${RES_PATH}/another_resource.robot
Ressource         ${RES_PATH}/more_resources/${RES NAME}
Ressource         ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Variablen         ../resources/varz.py
Variablen         ../resources/dynamic_varz.py    ${ARG}
Variablen         en/full_en.yaml    # This is a comment
Variablen         en/full_en.json    # This is a comment
Variablen         en/full_en.py    # This is a comment
Variablen         ${RES_PATH}/more_varz.py
Bibliothek        ${technology lib}    # defined in varz.py | |
Bibliothek        ${operating system}    # defined in another_resource.robot | |

*** Variablen ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Kommentare ***
This is a comments block
Second line of comments
*** Testfälle ***
My Test
    [Dokumentation]    This is _test_ *case* documentation
    [Marker]    test 1
    [Vorbereitung]    My Overriding Test Setup
    Log    Nothing to see
    [Nachbereitung]    My Overriding Test Teardown

first test
    [Dokumentation]    3-This is the documentation\n4-A continued line of documentation
    [Marker]    first    second
    [Vorbereitung]    Log To Console    Test Setup
    [Zeitlimit]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Ja'
    ${second}=    Check Logic    'Aus'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Nachbereitung]    Log To Console    Test Teardown

second test
    [Marker]    first    second    # This is a comment
    [Vorbereitung]    Log To Console    Test Setup    # This is a comment
    [Vorlage]    First Keyword    # This is a comment
    [Zeitlimit]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Nachbereitung]    Log To Console    Test Teardown    # This is a comment

third test
    Angenommen "Mr. Smith" is registered
    Und "cart" has objects
    Wenn "Mr. Smith" clicks in checkout
    Dann the total is presented and awaits confirmation
    Aber it is shown the unavailable payment method

*** Schlüsselwörter ***
My Suite Teardown
    [Argumente]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Dokumentation]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Zeitlimit]
    No Operation

First Keyword
    [Argumente]    ${arg}=None    @{no_list}    # This is a comment
    [Dokumentation]    5-This is the documentation\n\n7-A continued line of documentation
    [Marker]    first    second    # This is a comment
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
