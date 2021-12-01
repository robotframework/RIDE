*** Settings ***
Resource          ../external_resources/subdirectory2/bar.robot
Resource          ../external_resources/subdirectory/Foo.robot
Resource          ../external_resources/subdirectory2/Resource.robot

*** Test Cases ***
Test case
    kw1
    kw2

