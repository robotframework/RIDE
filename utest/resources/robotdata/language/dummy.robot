# This is a dummy file to be translated, without caring for validation.
Language: English

*** Settings ***
Library           Process
Library           OperatingSystem    AS    OS
Resource          my_resource.resource
Variables         my_variables.py
Documentation     This is the documentation 1st line.
...               Second line of documentation.
Metadata          NewData    NewValue
Name              This is the test suite name
Suite Setup       Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Suite Teardown    Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Test Setup        Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Task Setup        Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Test Teardown     Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Task Teardown     Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Test Template     Example Template
Task Template     Example Template
Test Timeout      5 seconds
Task Timeout      5 seconds
Test Tags         one    two    three
Task Tags         four    five    six

*** Variables ***
${m scalar}=      abc
@{m list}         cde    123    ${456}    ${7.89101}
&{m dict}=        a=a1    b=b2    c=c3
  
*** Test Cases ***
My first test
    [Tags]    one    two
    [Timeout]    10 seconds
    [Documentation]     This is the documentation 1st line.
    ...
    ...               Second line of documentation after empty line.
    No Operation
    # The word no is in logic values and is translated.
    
*** Tasks ***
My first task
    [Documentation]     This is the documentation 1st line.
    ...
    ...               Second line of documentation after empty line.
    [Template]    Example Template
    data    values
    type    data
    name    first
    
*** Comments ***
Fist line of comment.
Second line of comment.

*** Keywords ***
Example Template
   [Keyword Tags]    k_one    k_two
   [Setup]    Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
   ...      Third    arg4
   [Teardown]    Log    This is a log step
   [Documentation]     This is the documentation 1st line.
    ...
    ...               Second line of documentation after empty line.
   [Arguments]   ${arg1}=test    ${arg2}=123
   Log    ${arg1} ${arg2}

My Gherkin Keyword
    Given a sentence
    When it makes sense
    Then there is some meaning
    And we can learn something
    But it may not be useful.

My Logical Keyword
    FOR    ${logical}    IN    True    Yes    On
         Log    ${logical}
    END
    FOR    ${logical}    IN    False    No    Off
         Log    ${logical}
    END    

