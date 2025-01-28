*** Settings ***
Library           ./res.py

*** Keywords ***
keyword1
    [Arguments]    ${a}
    log    ${a} This is at Sub/Resources/res02.resource
    Run Keyword    keyword3

keyword2
    [Arguments]    ${a}
    log    ${a}

keyword3
    res_kw
