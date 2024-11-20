*** Settings ***
Resource          resources/resource.resource

*** Test Cases ***
Call keyword
    VAR    ${action}    Sends
    User ${action} Email
    User Reads Email

Server keyword
    VAR    ${action}    Sends Email
    resource.Server ${action} To User    John Doe
    VAR    ${user}    Jane Doe
    resource.Server Sends Message To User    ${user}
