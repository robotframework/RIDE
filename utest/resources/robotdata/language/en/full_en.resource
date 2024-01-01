# This is the preamble
Language: English

# A blank line

*** Settings ***
Library    Collections    # This is a comment
Resource       full_en.resource    # This is a comment
Variables      full_en.yaml    # This is a comment
Variables      full_en.json    # This is a comment
Variables      full_en.py    # This is a comment

Documentation    This is the documentation
...    A continued line of documentation

*** Variables ***
${myvar}    123    # This is a comment

*** Comments ***
This is a comments block
Second line of comments

*** Keywords ***
First Resource Keyword
    [Documentation]    This is the documentation
    ...    A continued line of documentation
    [Arguments]    ${arg}=None    # This is a comment
    [Tags]    first    second    # This is a comment
    Log To Console    This is the first resource keyword

Check Logic
    [Documentation]    Returns True if arg in ['True', 'Yes', 'On']
    ...               \nor returns False if arg in ['False', 'No', 'Off']
    [Arguments]    ${arg}='True'    # This is a comment
    [Tags]    logic    # This is a comment
    IF    ${arg}    # This is a comment
        Log    Arg it is True: arg=${arg}
        RETURN    Yes
    ELSE
        Log    Arg it is False: arg=${arg}
        RETURN    No
    END

${user} is registered
    No Operation

${cart} has objects
    No Operation

${user} clicks in checkout
    No Operation

the total is presented and awaits confirmation
    No Operation

it is shown the unavailable payment method
    No Operation

