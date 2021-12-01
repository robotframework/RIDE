*** Setting ***
Library           AnotherArgLib    ${param1}    \    ${param1} here too: ${param2}    ${param2}

*** Variable ***
@{RESOURCE 2 List VARIABLE}    1    2    3    4
${param1}         An interesting value
${param2}         Hello

*** Keyword ***
Resource2 UK
    [Timeout]
    No Operation
