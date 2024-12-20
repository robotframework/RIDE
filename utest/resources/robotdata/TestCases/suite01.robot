*** Settings ***
Suite Setup       external_res.keyword2    Called from Suite Setup on Suite01
Resource          ./resources/res01.resource
Resource          ./Sub/resources/res02.resource
Library           ./mykw.py
Resource          ../resources/external_res.resource

*** Test Cases ***
case01
    res02.keyword2    aaaa\na\na
    [Teardown]    res02.keyword1    Called from Teardown on case01

case02
    [Setup]    external_res.keyword1    Called from Setup on case02
    log    ${CURDIR}    console=True
    log    ${EXECDIR}    console=True
    my_kw
    res02.keyword1    hehe

case03
    res02.keyword3
    res01.keyword3
    Run Keyword    external_res.keyword3
