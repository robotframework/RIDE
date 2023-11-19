# This is the preamble
Language: English

# A blank line

*** Test Cases ***
First Test
    No Operation
    First Keyword
    Log To Console    Test execution with success

*** Keywords ***
First Keyword
    [Arguments]    ${arg}=None    # This is a comment
    Log To Console    This is First Keyword
