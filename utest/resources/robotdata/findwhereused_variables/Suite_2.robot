*** Settings ***
Resource  Res1.robot

*** Test Cases ***
Case 4
  ${True}

Case 5
  [Documentation]  See, if we can use the variable ${resVar} from a resource file
  Log  ${resVar}
  ${ServerHost}

Case 6
  [Documentation]  lorem ${False} ipsum
  [Setup]  ${True}
  ${True}

