
from visitante_repository import (
    cadastrar_visitante,
    buscar_visitante_por_id,
    listar_visitantes
)


# Cadastrar visitante
visitante_id = cadastrar_visitante(
    nome="Rafael",
    documento="12345678900",
    telefone="11999999999"
)

print("Visitante cadastrado!")
print("ID:", visitante_id)


# Buscar visitante
visitante = buscar_visitante_por_id(
    visitante_id
)

print("\nVisitante encontrado:")
print(visitante)


# Listar visitantes
print("\nLista de visitantes:")

for visitante in listar_visitantes():
    print(
        visitante["id"],
        visitante["nome"],
        visitante["ativo"]
    )
