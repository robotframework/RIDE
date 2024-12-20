*** Settings ***
Resource          ./resources/res02.resource
Library           ./Lib/mykw.py
Resource          ../../resources/external_res.resource

*** Test Cases ***
case01
    [Setup]    res02.keyword1    Called from Setup in Sub/Suite02/case01
    my_kw
    res02.keyword3
    external_res.keyword2    Called fromSteps on Sub/Suite02/case01
    [Teardown]    external_res.keyword3
