# This is the preamble
Language: Spanish

# A blank line

*** Configuraciones ***
Documentación     This test data file is used in *RobotIDE* _integration_ tests.
...               1-This is another line of the documentation
...               2-A continued line of documentation
Configuración de la Suite    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Desmontaje de la Suite    My Suite Teardown    ${scalar}    @{LIST}
Configuración de prueba    My Test Setup
Etiquetas de la prueba    new_tag    ride    regeression    # Comment on Tags
Metadatos         My Meta    data
Biblioteca        seleniumlibrary    # Purposefully wrong case | |
Biblioteca        Process    # This is a comment
Recursos          en/full_en.resource
Biblioteca        LibSpecLibrary
Biblioteca        ${LIB NAME}
Biblioteca        ArgLib    ${ARG}
Recursos          ../resources/resource.resource
Recursos          ../resources/resource2.robot
Recursos          PathResource.robot
Recursos          ../resources/resource.robot
Recursos          ${RES_PATH}/another_resource.robot
Recursos          ${RES_PATH}/more_resources/${RES NAME}
Recursos          ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Variable          ../resources/varz.py
Variable          ../resources/dynamic_varz.py    ${ARG}
Variable          en/full_en.yaml    # This is a comment
Variable          en/full_en.json    # This is a comment
Variable          en/full_en.py    # This is a comment
Variable          ${RES_PATH}/more_varz.py
Biblioteca        ${technology lib}    # defined in varz.py | |
Biblioteca        ${operating system}    # defined in another_resource.robot | |

*** Variables ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c
...               d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Comentarios ***
This is a comments block
Second line of comments
*** Casos de prueba ***
My Test
    [Documentación]    This is _test_ *case* documentation
    [Etiquetas]    test 1
    [Configuración]    My Overriding Test Setup
    Log    Nothing to see
    [Desmontaje]    My Overriding Test Teardown

first test
    [Documentación]    3-This is the documentation
    ...    4-A continued line of documentation
    [Etiquetas]    first    second
    [Configuración]    Log To Console    Test Setup
    [Tiempo agotado]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Si'
    ${second}=    Check Logic    'Off'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Desmontaje]    Log To Console    Test Teardown

second test
    [Etiquetas]    first    second    # This is a comment
    [Configuración]    Log To Console    Test Setup    # This is a comment
    [Plantilla]    First Keyword    # This is a comment
    [Tiempo agotado]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Desmontaje]    Log To Console    Test Teardown    # This is a comment

third test
    Dado "Mr. Smith" is registered
    Y "cart" has objects
    Cuando "Mr. Smith" clicks in checkout
    Entonces the total is presented and awaits confirmation
    Pero it is shown the unavailable payment method

*** Palabras clave ***
My Suite Teardown
    [Argumentos]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Documentación]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Tiempo agotado]
    No Operation

First Keyword
    [Argumentos]    ${arg}=None    @{no_list}    # This is a comment
    [Documentación]    5-This is the documentation
    ...
    ...    7-A continued line of documentation
    [Etiquetas]    first    second    # This is a comment
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
