# This is the preamble
Language: Hindi

# A blank line

*** स्थापना ***
प्रलेखन           This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
जांच की शुरुवात    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Suite Teardown    My Suite Teardown    ${scalar}    @{LIST}
Test Setup        My Test Setup
Test Teardown     My Overriding Test Teardown
जाँचका उपनाम      new_tag    ride    regeression    # Comment on Tags
अधि-आंकड़ा        My Meta    data
कोड़ प्रतिबिंब संग्रह    seleniumlibrary    # Purposefully wrong case | |
कोड़ प्रतिबिंब संग्रह    Process    # This is a comment
संसाधन            en/full_en.resource
कोड़ प्रतिबिंब संग्रह    LibSpecLibrary
कोड़ प्रतिबिंब संग्रह    ${LIB NAME}
कोड़ प्रतिबिंब संग्रह    ArgLib    ${ARG}
संसाधन            ../resources/resource.resource
संसाधन            ../resources/resource2.robot
संसाधन            PathResource.robot
संसाधन            ../resources/resource.robot
संसाधन            ${RES_PATH}/another_resource.robot
संसाधन            ${RES_PATH}/more_resources/${RES NAME}
संसाधन            ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
चर                ../resources/varz.py
चर                ../resources/dynamic_varz.py    ${ARG}
चर                en/full_en.yaml    # This is a comment
चर                en/full_en.json    # This is a comment
चर                en/full_en.py    # This is a comment
चर                ${RES_PATH}/more_varz.py
कोड़ प्रतिबिंब संग्रह    ${technology lib}    # defined in varz.py | |
कोड़ प्रतिबिंब संग्रह    ${operating system}    # defined in another_resource.robot | |

*** चर ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** टिप्पणी ***
This is a comments block
Second line of comments
*** नियत कार्य प्रवेशिका ***
My Test
    [प्रलेखन]    This is _test_ *case* documentation
    [निशान]    test 1
    [व्यवस्थापना]    My Overriding Test Setup
    Log    Nothing to see
    [विमोचन]    My Overriding Test Teardown

first test
    [प्रलेखन]    3-This is the documentation\n4-A continued line of documentation
    [निशान]    first    second
    [व्यवस्थापना]    Log To Console    Test Setup
    [समय समाप्त]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'निश्चित'
    ${second}=    Check Logic    'हालाँकि'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [विमोचन]    Log To Console    Test Teardown

second test
    [निशान]    first    second    # This is a comment
    [व्यवस्थापना]    Log To Console    Test Setup    # This is a comment
    [साँचा]    First Keyword    # This is a comment
    [समय समाप्त]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [विमोचन]    Log To Console    Test Teardown    # This is a comment

third test
    दिया हुआ "Mr. Smith" is registered
    और "cart" has objects
    जब "Mr. Smith" clicks in checkout
    तब the total is presented and awaits confirmation
    परंतु it is shown the unavailable payment method

*** कुंजीशब्द ***
My Suite Teardown
    [प्राचल]    ${scalar arg}    ${default arg}=default    @{list arg}
    [प्रलेखन]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [समय समाप्त]
    No Operation

First Keyword
    [प्राचल]    ${arg}=None    @{no_list}    # This is a comment
    [प्रलेखन]    5-This is the documentation\n\n7-A continued line of documentation
    [निशान]    first    second    # This is a comment
    Log To Console    This is the first keyword

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
