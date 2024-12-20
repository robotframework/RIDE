*** Settings ***
Library           res.py
Library           Sub/Lib/res2.py    # Another comment

*** Keywords ***
kw1
    [Arguments]    ${a}
    log    ${a}    # teste
    # comment test testst
    log    ${a}

keyword2
    [Arguments]    ${a}
    log    ${a}
    Log To Console    This is the argument \${a} = ${a} !

keyword3
    res kw
    res2.res kw 2    # Kw from res2 with a space in calling

kw4
    Comment    res kw
    Comment    res kw 2
    No Operation

kw5
    res.kw 2    # teste teste
    res.kw
    res2.Res Kw 2
