# This is the preamble
Language: Japanese

# A blank line

*** 設定 ***
ドキュメント            This test data file is used in *RobotIDE* _integration_ test
...               1-This is another line of the documentation
...               2-A continued line of documentation
スイート セットアップ       Run Keywords    Log To Console    Suite Setup
...               AND    Log    Test
...               AND    Log to Console    Test
...               AND    My Suite Setup
スイート ティアダウン       My Suite Teardown    ${scalar}    @{LIST}
テスト セットアップ        My Test Setup
テスト ティアダウン        My Overriding Test Teardown
テスト タグ            new_tag    ride    regeression    # Comment on Tags
メタデータ             My Meta    data
ライブラリ             seleniumlibrary    # Purposefully wrong case | |
ライブラリ             Process    # This is a comment
リソース              en/full_en.resource
ライブラリ             LibSpecLibrary
ライブラリ             ${LIB NAME}
ライブラリ             ArgLib    ${ARG}
リソース              ../resources/resource.resource
リソース              ../resources/resource2.robot
リソース              PathResource.robot
リソース              ../resources/resource.robot
リソース              ${RES_PATH}/another_resource.robot
リソース              ${RES_PATH}/more_resources/${RES NAME}
リソース              ${RES_PATH}/more_resources${/}${EMPTY}even_more_resources.robot
変数                ../resources/varz.py
変数                ../resources/dynamic_varz.py    ${ARG}
変数                en/full_en.yaml    # This is a comment
変数                en/full_en.json    # This is a comment
変数                en/full_en.py    # This is a comment
変数                ${RES_PATH}/more_varz.py
ライブラリ             ${technology lib}    # defined in varz.py | |
ライブラリ             ${operating system}    # defined in another_resource.robot | |

*** 変数 ***
${SCALAR}         value
@{LIST}           1    2    3    4    a    b    c
...               d
${LIB NAME}       Collections
${RES_PATH}       ../resources
${ARG}            value
${myvar}          123    # This is a comment

*** コメント ***
This is a comments block
Second line of comments
*** テスト ケース ***
My Test
    [ドキュメント]    This is _test_ *case* documentation
    [タグ]    test 1
    [セットアップ]    My Overriding Test Setup
    Log    Nothing to see
    [ティアダウン]    My Overriding Test Teardown

first test
    [ドキュメント]    3-This is the documentation
    ...    4-A continued line of documentation
    [タグ]    first    second
    [セットアップ]    Log To Console    Test Setup
    [タイムアウト]    60
    First Keyword    nonsense
    ${first}=    Check Logic    '有効'
    ${second}=    Check Logic    'いいえ'
    Log Variables
    Log    Test executed with success, first=${first}, second=${second}
    [ティアダウン]    Log To Console    Test Teardown

second test
    [タグ]    first    second    # This is a comment
    [セットアップ]    Log To Console    Test Setup    # This is a comment
    [テンプレート]    First Keyword    # This is a comment
    [タイムアウト]    60    # This is a comment
    No Operation
    Log    this is ddt
    Log To Console    Test executed with success
    [ティアダウン]    Log To Console    Test Teardown    # This is a comment

third test
    仮定 "Mr. Smith" is registered
    および "cart" has objects
    条件 "Mr. Smith" clicks in checkout
    アクション the total is presented and awaits confirmation
    ただし it is shown the unavailable payment method

*** キーワード ***
My Suite Teardown
    [引数]    ${scalar arg}    ${default arg}=default    @{list arg}
    [ドキュメント]    This is *user* _keyword_ documentation
    Log    ${scalar arg}
    Log Many    @{list arg}
    [Return]    Success

Duplicate UK
    No Operation

My Test Setup
    [タイムアウト]
    No Operation

First Keyword
    [引数]    ${arg}=None    @{no_list}    # This is a comment
    [ドキュメント]    5-This is the documentation
    ...
    ...    7-A continued line of documentation
    [タグ]    first    second    # This is a comment
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
