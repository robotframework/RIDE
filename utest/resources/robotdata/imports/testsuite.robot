*** Settings ***
Resource          res//existing.robot
Resource          res//none_existing.robot
Resource          ${RESU}
Library           String    # A built in library from PYTHONPATH
Library           libs//existing.py
Library           libs//none_existing.py    AS    nothing
Library           libs//corrupted.py
Library           ${LIB}
Variables         ${CURDIR}//vars//vars.py
Variables         vars//none_existing.py

*** Variables ***
${RESU}           res//with_variable.robot
${LIB}            XML

*** Test Cases ***
Some case
    No Operation

Another case
    Log to Console    ${VARIABLE}