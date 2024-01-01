# This is the preamble
Language: English

# A blank line

*** Settings ***
Documentation    This is the documentation for Gherkin test
...    A continued line of documentation

*** Test Cases ***
third test
    Given "Mr. Smith" is registered
    And "cart" has objects
    When "Mr. Smith" clicks in checkout
    Then the total is presented and awaits confirmation
    But it is shown the unavailable payment method

*** Keywords ***
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

