# Este é o preâmbulo
Language: Portuguese

# Mais uma linha em branco

*** Comentários ***
This is a comments block
Second line of comments
Maybe this block is still in preamble

*** Definições ***
Biblioteca    Collections
Recurso       full_pt.resource
Variável      full_pt.yaml
Variável      full_pt.json
Variável      full_pt.py

Documentação    This is the documentation
...    A continued line of documentation

Metadados    Nome    Value

Inicialização de Suíte      Palavra-chave de Suite    Suite Setup
Finalização de Suíte        Log To Console    Suite Teardown

*** Variáveis ***
${myvar}    123

*** Comentários ***
This is a comments block
Second line of comments

*** Palavras-Chave ***
Palavra-chave de Suite
    [Documentação]    This is the documentation
    ...    A continued line of documentation
    [Argumentos]    ${arg}
    [Etiquetas]    suite
    Log To Console    Esta é a palavra-chave de Suíte arg=${arg}
