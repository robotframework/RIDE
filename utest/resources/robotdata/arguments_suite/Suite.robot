*** Variables ***
@{LIST_VARIABLE}  1  2  3
&{DICT_VARIABLE}  key=val  anotherone=bites the dust

*** Test Cases ***
Keissi
  KW1  arg1

*** Keywords ***
KW1
  [Arguments]  ${mandatory}  ${optional}=
  No Operation

KW2
  [Arguments]  @{rest}
  No Operation

KW3
  FOR  ${i}  IN  1  2
    Log  jee
    Log  ${i}
    Log  ${unknown}
  END
  FOR  ${j}  IN RANGE  200
    Log  moi taas
  END

KW4
  [Arguments]  ${optional}=val  @{others}
  No Operation

KW5
  [Arguments]  ${mandatory1}  ${mandatory2}
  Log  ${mandatory1}
  Log  ${mandatory2}
  No Operation
