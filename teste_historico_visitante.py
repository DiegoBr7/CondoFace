
from historico_repository import registrar_historico

registrar_historico(
    visitante_id=1,
    resultado="NEGADO",
    motivo="TESTE - Acesso negado"
)

print("Teste de histórico de visitante concluído!")
