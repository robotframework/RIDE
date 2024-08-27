# This is the preamble
Language: Turkish

# A blank line

*** Ayarlar ***
Dokümantasyon     This test data file is used in *RobotIDE* _integration_ tests.\n1-This is another line of the documentation\n2-A continued line of documentation
Takım Kurulumu    Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
Takım Bitişi      My Suite Teardown    ${scalar}    @{LIST}
Test Kurulumu     My Test Setup
Test Bitişi       My Overriding Test Teardown
Test Etiketleri    new_tag    ride    regeression    # Comment on Tags
Üstveri           My Meta    data
Kütüphane         seleniumlibrary    # Purposefully wrong case | |
Kütüphane         Process    # This is a comment
Kaynak            en/full_en.resource
Kütüphane         LibSpecLibrary
Kütüphane         ${LIB NAME}
Kütüphane         ArgLib    ${ARG}
Kaynak            ../resources/resource.resource
Kaynak            ../resources/resource2.robot
Kaynak            PathResource.robot
Kaynak            ../resources/resource.robot
Kaynak            ${RES_PATH}/another_resource.robot
Kaynak            ${RES_PATH}/more_resources/${RES NAME}
Kaynak            ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
Değişkenler       ../resources/varz.py
Değişkenler       ../resources/dynamic_varz.py    ${ARG}
Değişkenler       en/full_en.yaml    # This is a comment
Değişkenler       en/full_en.json    # This is a comment
Değişkenler       en/full_en.py    # This is a comment
Değişkenler       ${RES_PATH}/more_varz.py
Kütüphane         ${technology lib}    # defined in varz.py | |
Kütüphane         ${operating system}    # defined in another_resource.robot | |

*** Değişkenler ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c    d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** Yorumlar ***
This is a comments block
Second line of comments
*** Test Durumları ***
My Test
    [Dokümantasyon]    This is _test_ *case* documentation
    [Etiketler]    test 1
    [Kurulum]    My Overriding Test Setup
    Log    Nothing to see
    [Bitiş]    My Overriding Test Teardown

first test
    [Dokümantasyon]    3-This is the documentation\n4-A continued line of documentation
    [Etiketler]    first    second
    [Kurulum]    Log To Console    Test Setup
    [Zaman Aşımı]    60
    First Keyword    nonsense
    ${first}=    Check Logic    'Evet'
    ${second}=    Check Logic    'Kapali'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [Bitiş]    Log To Console    Test Teardown

second test
    [Etiketler]    first    second    # This is a comment
    [Kurulum]    Log To Console    Test Setup    # This is a comment
    [Taslak]    First Keyword    # This is a comment
    [Zaman Aşımı]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [Bitiş]    Log To Console    Test Teardown    # This is a comment

third test
    Diyelim ki "Mr. Smith" is registered
    Ve "cart" has objects
    Eğer ki "Mr. Smith" clicks in checkout
    O zaman the total is presented and awaits confirmation
    Ancak it is shown the unavailable payment method

*** Anahtar Kelimeler ***
My Suite Teardown
    [Argümanlar]    ${scalar arg}    ${default arg}=default    @{list arg}
    [Dokümantasyon]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [Zaman Aşımı]
    No Operation

First Keyword
    [Argümanlar]    ${arg}=None    @{no_list}    # This is a comment
    [Dokümantasyon]    5-This is the documentation\n\n7-A continued line of documentation
    [Etiketler]    first    second    # This is a comment
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
