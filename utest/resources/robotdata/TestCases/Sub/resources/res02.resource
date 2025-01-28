*** Settings ***
Library           ./res.py

*** Keywords ***
keyword11
    [Arguments]    ${a}
    log    ${a} This is at Sub/Resources/res02.resource
    Run Keyword    keyword33

keyword2
    [Arguments]    ${a}
    log    ${a}

keyword33
    res_kw
