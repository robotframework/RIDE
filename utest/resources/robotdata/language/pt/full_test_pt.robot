# Este é o preâmbulo
Language: Portuguese

# Mais uma linha em branco

*** Comentários ***
This is the preamble comments block
Second line of comments
Maybe this block is still in preamble
# Comment inside preamble comments block

*** Definições ***
Biblioteca    Process
Recurso       full_pt.resource
Variável      full_pt.yaml
Variável      full_pt.json
Variável      full_pt.py
# Comment inside settings block, next is empty line followed by documention

Documentação    This is the documentation
...    A continued line of documentation

Metadados    Nome    Value
# Comment inside settings block after metadata, next is empty line followed by suite setup

Inicialização de Suíte      No Operation
Finalização de Suíte        No Operation
# Comment inside settings block after suite teardown, next is empty line followed by variables section

*** Variáveis ***
${myvar}    123
# Comment inside variables, next is empty line followed by a comments section

*** Comentários ***
This is a comments block
Second line of comments
# Comment inside second comments block

*** Casos de Teste ***
teste primeiro
    [Documentação]    This is the documentation
    ...    A continued line of documentation
    [Inicialização]    Log To Console    Test Setup
    [Finalização]    Log To Console    Test Teardown
    [Tempo Limite]    60
    [Etiquetas]    first    second
    Primeira palavra-chave
    # Comment inside test case, next is empty line followed by steps

    ${primeira}=    Verifica Lógica    'Sim'
    ${segunda}=    Verifica Lógica    'Desligado'
    Log Variables
    Log    Tarefa executada com sucesso, primeira=${primeira}, segunda=${segunda}
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
${carrinho de compras} tem objectos
    No Operation

${utilizador} clica em finalizar compra
    No Operation

é apresentado o total e aguarda confirmação
    No Operation

é apresentado meio de pagamento indisponível
    No Operation

