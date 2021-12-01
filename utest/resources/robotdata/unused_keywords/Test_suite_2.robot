*** Settings ***
Resource          Res1.robot
Resource          foobar.robot

*** Test Cases ***
Another test case
    Do that
    Local keyword

*** Keywords ***
Local keyword
    Log    Hello

