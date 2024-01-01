# Este é o preâmbulo
Language: Portuguese

# Mais uma linha em branco

*** Comentários ***
This is a comments block
Second line of comments
Maybe this block is still in preamble

*** Definições ***
Biblioteca    Collections    # Isto é um comentário
Recurso       full_pt.resource    # Isto é um comentário
Variável      full_pt.yaml    # Isto é um comentário
Variável      full_pt.json    # Isto é um comentário
Variável      full_pt.py    # Isto é um comentário

Documentação    This is the documentation
...    A continued line of documentation

Metadados    Nome    Valor    # Isto é um comentário

Inicialização de Suíte      Palavra-chave de Suite    Suite Setup
Finalização de Suíte        Log To Console    Suite Teardown

*** Variáveis ***
${myvar}    123    # Isto é um comentário

*** Comentários ***
This is a comments block
Second line of comments

*** Palavras-Chave ***
Palavra-chave de Suite
    [Documentação]    This is the documentation
    ...    A continued line of documentation
    [Argumentos]    ${arg}    # Isto é um comentário
    [Etiquetas]    suite    # Isto é um comentário
    Log To Console    Esta é a palavra-chave de Suíte arg=${arg}
