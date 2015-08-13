*** Test Cases ***
Keissi   KW1

*** Variables ***
@{LIST_VARIABLE}  1  2  3
&{DICT_VARIABLE}  key=val   anotherone=bites the dust

*** Keywords ***
KW1
    [Arguments]    ${mandatory}    ${optional}=

KW2
    [Arguments]    @{rest}

KW3
    : FOR    ${i}    IN    1    2
    \    Log    jee
    \    Log    ${i}
    \    Log    ${unknown}
    : FOR    ${j}    IN RANGE    200
    \    Log    moi taas

KW4
    [Arguments]  ${optional}=val  @{others}
    No Operation

KW5
    [Arguments]  ${mandatory1}  ${mandatory2}
    Log  ${mandatory1}
    Log  ${mandatory2}
