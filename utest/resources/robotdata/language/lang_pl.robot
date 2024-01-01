# This is the preamble
Language: Polish

# A blank line

*** Variables ***
&{error}          name=err

*** Comments ***
This is a comments block  
Second line of comments  
Maybe this block is still in preamble  
One more line  
  
*** Przypadki Testowe ***
First Test
    No Operation
    First Keyword
    Log To Console    Test execution with success

*** Słowa Kluczowe ***
First Keyword
    [Argumenty]    ${arg}=None    # This is a comment
    Log To Console    This is First Keyword
    No Operation
    Log To Console    One more line
