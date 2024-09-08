# This is a dummy file to be translated, without caring for validation.
Language: Portuguese

*** Definições ***
Biblioteca           Process
Biblioteca           OperatingSystem    AS    OS
Recurso          my_resource.resource
Variável         my_variables.py
Documentação     This is the documentation 1st line.
...               Second line of documentation.
Metadados          NewData    NewValue
Nome              This is the test suite name
Inicialização de Suíte       Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Finalização de Suíte    Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Inicialização de Teste        Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Inicialização de Tarefa        Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Finalização de Teste     Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Finalização de Tarefa     Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Modelo de Teste     Example Template
Modelo de Tarefa     Example Template
Tempo Limite de Teste      5 seconds
Tempo Limite de Tarefa      5 seconds
Etiquetas de Testes         one    two    three
Etiquetas de Tarefas         four    five    six

*** Variáveis ***
${m scalar}=      abc
@{m list}         cde    123    ${456}    ${7.89101}
&{m dict}=        a=a1    b=b2    c=c3
  
*** Casos de Teste ***
My first test
    [Etiquetas]    one    two
    [Tempo Limite]    10 seconds
    [Documentação]     This is the documentation 1st line.
    ...
    ...               Second line of documentation after empty line.
    No Operation
    # The word no is in logic values and is translated.
    
*** Tarefas ***
My first task
    [Documentação]     This is the documentation 1st line.
    ...
    ...               Second line of documentation after empty line.
    [Modelo]    Example Template
    data    values
    type    data
    name    first
    
*** Comentários ***
Fist line of comment.
Second line of comment.

*** Palavras-Chave ***
Example Template
   [Etiquetas de Palavras-Chave]    k_one    k_two
   [Inicialização]    Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
   ...      Third    arg4
   [Finalização]    Log    This is a log step
   [Documentação]     This is the documentation 1st line.
    ...
    ...               Second line of documentation after empty line.
   [Argumentos]   ${arg1}=test    ${arg2}=123
   Log    ${arg1} ${arg2}

My Gherkin Keyword
    Dado a sentence
    Quando it makes sense
    Então there is some meaning
    E we can learn something
    Mas it may not be useful.

My Logical Keyword
    FOR    ${logical}    IN    Verdadeiro    Verdade    Sim
         Log    ${logical}
    END
    FOR    ${logical}    IN    Falso    Não    Desligado
         Log    ${logical}
    END    

