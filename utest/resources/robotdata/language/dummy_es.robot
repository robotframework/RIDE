# This is a dummy file to be translated, without caring for validation.
Language: Spanish

*** Configuraciones ***
Biblioteca           Process
Biblioteca           OperatingSystem    AS    OS
Recursos          my_resource.resource
Variable         my_variables.py
Documentación     This is the documentation 1st line.
...               Second line of documentation.
Metadatos          NewData    NewValue
Nombre              This is the test suite name
Configuración de la Suite       Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Desmontaje de la Suite    Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Configuración de prueba        Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Configuración de tarea        Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Desmontaje de la prueba     Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Desmontaje de tareas     Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
...               Third    arg4
Plantilla de prueba     Example Template
Plantilla de tareas     Example Template
Tiempo de espera de la prueba      5 seconds
Tiempo de espera de las tareas      5 seconds
Etiquetas de la prueba         one    two    three
Etiquetas de las tareas         four    five    six

*** Variables ***
${m scalar}=      abc
@{m list}         cde    123    ${456}    ${7.89101}
&{m dict}=        a=a1    b=b2    c=c3
  
*** Casos de prueba ***
My first test
    [Etiquetas]    one    two
    [Tiempo agotado]    10 seconds
    [Documentación]     This is the documentation 1st line.
    ...
    ...               Second line of documentation after empty line.
    No Operation
    # The word no is in logic values and is translated.
    
*** Tareas ***
My first task
    [Documentación]     This is the documentation 1st line.
    ...
    ...               Second line of documentation after empty line.
    [Plantilla]    Example Template
    data    values
    type    data
    name    first
    
*** Comentarios ***
Fist line of comment.
Second line of comment.

*** Palabras clave ***
Example Template
   [Etiquetas de palabras clave]    k_one    k_two
   [Configuración]    Run Keywords    First     arg1    AND    Second    arg2    arg3    AND
   ...      Third    arg4
   [Desmontaje]    Log    This is a log step
   [Documentación]     This is the documentation 1st line.
    ...
    ...               Second line of documentation after empty line.
   [Argumentos]   ${arg1}=test    ${arg2}=123
   Log    ${arg1} ${arg2}

My Gherkin Keyword
    Dado a sentence
    Cuando it makes sense
    Entonces there is some meaning
    Y we can learn something
    Pero it may not be useful.

My Logical Keyword
    FOR    ${logical}    IN    Verdadero    Si    On
         Log    ${logical}
    END
    FOR    ${logical}    IN    Falso    No    Off
         Log    ${logical}
    END    

