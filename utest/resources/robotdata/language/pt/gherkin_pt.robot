# Este é o preâmbulo
Language: Portuguese

# Mais uma linha em branco

*** Definições ***
Documentação      Esta é a documentação para o teste Gherkin
...               Uma linha de continuação da documentação

*** Casos de Teste ***
teste terceiro
    Dado "Sr. José" está registado
    E "carrinho" tem objectos
    Quando "Sr. José" clica em finalizar compra
    Então é apresentado o total e aguarda confirmação
    Mas é apresentado meio de pagamento indisponível
    # Comment at end of test case, next is empty line followed by the section keywords

*** Palavras-Chave ***
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
