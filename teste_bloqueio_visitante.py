
from autorizacao_visitante_repository import (
    buscar_autorizacao_visitante
)

visitante_id = 1

autorizacao = buscar_autorizacao_visitante(
    visitante_id
)

if autorizacao is None:
    print("ACESSO NEGADO")
    print("Visitante sem autorizacao valida.")
else:
    print("ACESSO PERMITIDO")
