*** Settings ***
Library           Collections
Resource          ../resources/res01.resource
Library           ./Lib/SubMyListener.py
Library           ../Sub/Lib/mykw.py

*** Test Cases ***
case01
    [Setup]    res01.keyword3
    keyword2    lalala\nlala\nlala

case02
    log    ${CURDIR}
    log    ${EXECDIR}
    my_kw
    kw1    hehe
    after navigate to    about:blank    None
