*** Keywords ***
UK From Variable Resource  No Operation

*** Variables ***
${library_from_resource}  Dialogs
${resource_from_resource}  resource_from_resource_with_variable.robot

*** Settings ***
Library  ${library_from_resource}
Resource  ${resource_from_resource}
