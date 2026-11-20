from morador_repository import buscar_morador_por_nome

morador = buscar_morador_por_nome("Edy")

if morador is not None:
    print("Morador encontrado!")
    print("Nome:", morador["nome"])
    print("Bloco:", morador["bloco"])
    print("Apartamento:", morador["apartamento"])
    print("Ativo:", bool(morador["ativo"]))
else:
    print("Morador não encontrado!")