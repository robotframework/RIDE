# Este é o preâmbulo
Language: Portuguese

# Mais uma linha em branco

*** Comentários ***
This is the preamble and first comments block
Second line of comments    # Isto é um comentário
Maybe this block is still in preamble
# Comment inside preamble comments block

*** Definições ***
Biblioteca    Process    # Isto é um comentário
Variável      full_pt.yaml    # Isto é um comentário
Variável      full_pt.json    # Isto é um comentário
Variável      full_pt.py    # Isto é um comentário
Recurso       full_pt.resource
# Comment inside settings block, next is empty line followed by documentation

Documentação    This is the documentation
...    A continued line of documentation    # Isto é um comentário

Metadados    Nome    Valor    # Isto é um comentário # Comment inside settings block after metadata, next is empty line followed by suite setup

Inicialização de Suíte      No Operation    # Isto é um comentário
Finalização de Suíte        No Operation    # Isto é um comentário # Comment inside settings block after suite teardown, next is empty line followed by variables section

*** Comentários ***
This is the second comments block after settings
Second line of comments    # Isto é um comentário 
# Comment inside second comments block

*** Variáveis ***
${myvar}    123    # Isto é um comentário # Comment inside variables, next is empty line followed by a comments section

*** Comentários ***
This is the third comments block after variables
Second line of comments    # Isto é um comentário
# Comment inside second comments block

*** Casos de Teste ***
teste primeiro
    [Documentação]    This is the documentation
    ...    A continued line of documentation    # Isto é um comentário
    [Inicialização]    Log To Console    Test Setup    # Isto é um comentário
    [Finalização]    Log To Console    Test Teardown    # Isto é um comentário
    [Tempo Limite]    60    # Isto é um comentário
    [Etiquetas]    first    second    # Isto é um comentário
    Primeira palavra-chave    # Isto é um comentário
    # Comment inside test case, next is empty line followed by steps

    Log    First step after empty line
    # ${primeira}=    Verifica Lógica    'Sim'
    # ${segunda}=    Verifica Lógica    'Desligado'
    Log Variables
    # Log    Tarefa executada com sucesso, primeira=${primeira}, segunda=${segunda}
    # Comment at end of test case, next is empty line followed another test case WITH a comment before name

# Comment before test case, next is test case name
teste segundo
    [Modelo]    Primeira palavra-chave
    [Inicialização]    Log To Console    Test Setup
    [Finalização]    Log To Console    Test Teardown
    [Tempo Limite]    60
    [Etiquetas]    first    second
    No Operation
    Primeira palavra-chave
    Log To Console    Teste executado com sucesso

teste terceiro
    Dado "Sr. José" está registado
    E "carrinho" tem objectos
    Quando "Sr. José" clica em finalizar compra
    Então é apresentado o total e aguarda confirmação
    Mas é apresentado meio de pagamento indisponível
    # Comment at end of test case, next is empty line followed by the section keywords

*** Comentários ***
This is the fourth comments block after test cases
Second line of comments    # Isto é um comentário
# Comment inside second comments block

*** Palavras-Chave ***
Primeira palavra-chave
    [Documentação]    This is the documentation
    ...    A continued line of documentation
    [Argumentos]    @{arg}
    [Etiquetas]    first    second
    Log To Console    Esta é a primeira palavra-chave arg=${arg}
    # Comment at end of keyword, next is empty line followed by another keyword

${utilizador} está registado
    No Operation

# Comment before keyword, next is keyword name
${carrinho de compras} tem objectos    # Isto é um comentário
    No Operation    # Isto é um comentário

${utilizador} clica em finalizar compra    # Isto é um comentário
    No Operation    # Isto é um comentário

é apresentado o total e aguarda confirmação
    No Operation

é apresentado meio de pagamento indisponível
    No Operation

*** Comentários ***
This is the fifth comments block after keywords
Second line of comments    # Isto é um comentário
# Comment inside last comments block

