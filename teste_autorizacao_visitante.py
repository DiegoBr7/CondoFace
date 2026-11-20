
from datetime import datetime, timedelta

from autorizacao_visitante_repository import (
    cadastrar_autorizacao,
    buscar_autorizacao_visitante
)

# IDs de exemplo do seu banco
visitante_id = 1  # Rafael
morador_id = 1    # Edy

agora = datetime.now()

inicio = agora - timedelta(minutes=5)
fim = agora + timedelta(hours=4)

autorizacao_id = cadastrar_autorizacao(
    visitante_id=visitante_id,
    morador_id=morador_id,
    inicio_validade=inicio,
    fim_validade=fim,
    motivo="Visita ao apartamento"
)

print("Autorizacao cadastrada!")
print("ID:", autorizacao_id)

autorizacao = buscar_autorizacao_visitante(
    visitante_id
)

if autorizacao:
    print("VISITANTE AUTORIZADO")
    print(autorizacao)
else:
    print("VISITANTE SEM AUTORIZACAO VALIDA")
