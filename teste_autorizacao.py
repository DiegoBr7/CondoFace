
from autorizacao_repository import buscar_autorizacao


morador_id = 1

autorizacao = buscar_autorizacao(morador_id)

if autorizacao is None:

    print("ACESSO NEGADO")
    print("Morador sem autorizacao cadastrada.")

elif autorizacao["permitido"]:

    print("ACESSO PERMITIDO")
    print("Motivo:", autorizacao["motivo"])

else:

    print("ACESSO NEGADO")
    print("Motivo:", autorizacao["motivo"])
