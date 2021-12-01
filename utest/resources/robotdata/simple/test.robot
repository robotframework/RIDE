*** Test Cases ***
Test Case
  Keyword  argument

*** Keywords ***
Keyword
  [Arguments]  ${argument}
  Log  ${argument}
  No Operation
  ${foo}=  Set Variable  value
  Log  ${foo}
  ${bar}=  Set Variable  value2
  Log  ${foo} and ${bar}
  : FOR  ${i}  IN  1  2  3
     Log  ${i}
  Log  ${i} out
