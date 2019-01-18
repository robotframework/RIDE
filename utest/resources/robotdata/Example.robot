*** Variables ***
${scalar}         1.234    # comentário
@{list}           2    a    4    b
&{dicionario}     def=inição    sig=nificado
${new var}        3    # esta é nova

*** Test Cases ***
test
    ${testvar}=    Set Variable    ${scalar}
    Set Test Variable    ${testvar}
    # DEBUG
    For Loop Example
    Log Many    &{dicionario}
    Log Variables    @{TEST_TAGS}

Téste líçhadõ
    Should Be Equal As Integers    3    3
    Log To Console    Vamos meter isto em Pausa. Linha comentário
    BuiltIn.Comment    PAUSE
    Opção Primeirª12    ${30}

*** Keywords ***
For Loop Example
    : FOR    ${index}    IN RANGE    0    5
    \    ${testvar} =    Evaluate    1 + ${index}
    \    ${total} =    Keyword that will use testvar
    Log    ${scalar}

Keyword that will use testvar
    ${returntotal} =    Evaluate    ${testvar}+1
    Log Many    ${scalar}    @{list}    &{dicionario}    ${new var}
    &{dicionario}=    No Operation
    @{list}=    No Operation
    [Return]    ${returntotal}

Opção Primeirª12
    [Arguments]    ${arg1}
    Log    Pálavrâs ComAÇENTOS
    Sleep    0.4 seconds
    Run Keyword If    ${arg1} < 6    Return From Keyword
    Opção Primeirª12    ${arg1-1}
