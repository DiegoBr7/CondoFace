
from identidade import (
    criar_identificador,
    separar_identificador
)

morador = criar_identificador(
    "morador",
    1
)

visitante = criar_identificador(
    "visitante",
    1
)

print("Morador:", morador)
print("Visitante:", visitante)

tipo, pessoa_id = separar_identificador(
    visitante
)

print("Tipo:", tipo)
print("ID:", pessoa_id)
