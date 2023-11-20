# Este é o preâmbulo
Language: Portuguese

# Mais uma linha em branco

*** Comentários ***
This is a comments block
Second line of comments
Maybe this block is still in preamble

*** Definições ***
Biblioteca    String
Variável      full_pt.yaml
Variável      full_pt.json
Variável      full_pt.py

Documentação    This is the documentation
...    A continued line of documentation

*** Variáveis ***
${myvar}    1234

*** Comentários ***
This is a comments block
Second line of comments

*** Palavras-Chave ***
Primeira palavra-chave do Recurso
    [Documentação]    This is the documentation
    ...    A continued line of documentation
    [Argumentos]    ${arg}=None
    [Etiquetas]    first    second
    Log To Console    Esta é a primeira palavra-chave do Recurso

Verifica Lógica
    [Documentação]    Retorna Verdadeiro se arg em ['Verdadeiro', 'Verdade', 'Sim', 'Ligado']
    ...               \nou retorna Falso se arg em ['Falso', 'Não', 'Desligado', 'Desativado', 'Nada']
    [Argumentos]    ${arg}='Verdadeiro'
    [Etiquetas]    lógica
    IF    ${arg}
        Log    Arg it True: arg=${arg}
        RETURN    Verdade
    ELSE
        Log    Arg it False: arg=${arg}
        RETURN    Não
    END

${utilizador} está registado
    No Operation

${carrinho de compras} tem objectos
    No Operation

${utilizador} clica em finalizar compra
    No Operation

é apresentado o total e aguarda confirmação
    No Operation

é apresentado meio de pagamento indisponível
    No Operation

