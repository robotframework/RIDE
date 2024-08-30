# This is the preamble
Language: Brazilian Portuguese

# A blank line

*** Configurações ***
Documentação      This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
Configuração da Suíte    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Finalização de Suíte    My Suite Teardown    ${scalar}    @{LIST}
Inicialização de Teste    My Test Setup
Finalização de Teste    My Overriding Test Teardown
Test Tags         new_tag    ride    regeression    # Comment on Tags
Metadados         My Meta    data
Biblioteca        seleniumlibrary    # Purposefully wrong case | |
Biblioteca        Process    # This is a comment
Recurso           en/full_en.resource
Biblioteca        LibSpecLibrary
Biblioteca        ${LIB NAME}
Biblioteca        ArgLib    ${ARG}
Recurso           ../resources/resource.resource
Recurso           ../resources/resource2.robot
Recurso           PathResource.robot
Recurso           ../resources/resource.robot
Recurso           ${RES_PATH}/another_resource.robot
Recurso           ${RES_PATH}/more_resources/${RES NAME}
Recurso           ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Variável          ../resources/varz.py
Variável          ../resources/dynamic_varz.py    ${ARG}
Variável          en/full_en.yaml    # This is a comment
Variável          en/full_en.json    # This is a comment
Variável          en/full_en.py    # This is a comment
Variável          ${RES_PATH}/more_varz.py
Biblioteca        ${technology lib}    # defined in varz.py | |
Biblioteca        ${operating system}    # defined in another_resource.robot | |

*** Variáveis ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Comentários ***
This is a comments block
Second line of comments
*** Casos de Teste ***
My Test
    [Documentação]    This is _test_ *case* documentation
    [Etiquetas]    test 1
    [Inicialização]    My Overriding Test Setup
    Log    Nothing to see
    [Finalização]    My Overriding Test Teardown

first test
    [Documentação]    3-This is the documentation\n4-A continued line of documentation
    [Etiquetas]    first    second
    [Inicialização]    Log To Console    Test Setup
    [Tempo Limite]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Verdade'
    ${second}=    Check Logic    'Desligado'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Finalização]    Log To Console    Test Teardown

second test
    [Etiquetas]    first    second    # This is a comment
    [Inicialização]    Log To Console    Test Setup    # This is a comment
    [Modelo]    First Keyword    # This is a comment
    [Tempo Limite]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Finalização]    Log To Console    Test Teardown    # This is a comment

third test
    Dado "Mr. Smith" is registered
    E "cart" has objects
    Quando "Mr. Smith" clicks in checkout
    Então the total is presented and awaits confirmation
    Mas it is shown the unavailable payment method

*** Palavras-Chave ***
My Suite Teardown
    [Argumentos]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Documentação]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Tempo Limite]
    No Operation

First Keyword
    [Argumentos]    ${arg}=None    @{no_list}    # This is a comment
    [Documentação]    5-This is the documentation\n\n7-A continued line of documentation
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
