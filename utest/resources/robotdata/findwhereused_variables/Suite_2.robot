*** Settings ***
Resource  Res1.robot

*** Test Cases ***
Case 4
  ${Truth}

Case 5
  [Documentation]  See, if we can use the variable ${resVar} from a resource file
  Log  ${resVar}
  ${ServerHost}

Case 6
  [Documentation]  lorem ${Falsy} ipsum
  [Setup]  ${Truth}
  ${Truth}

