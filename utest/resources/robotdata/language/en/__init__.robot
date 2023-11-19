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

Metadata    Name    Value    # This is a comment

Suite Setup           Suite Keyword    Suite Setup
Suite Teardown        Log To Console    Suite Teardown

*** Variables ***
${myvar}    123    # This is a comment

*** Comments ***
This is a comments block
Second line of comments

*** Keywords ***
Suite Keyword 
    [Documentation]    This is the documentation
    ...    A continued line of documentation
    [Arguments]    ${arg}    # This is a comment
    [Tags]    suite    # This is a comment
    Log To Console    This is the Suite Keyword arg=${arg}
