
def criar_identificador(tipo, pessoa_id):

    tipos_permitidos = (
        "morador",
        "visitante"
    )

    if tipo not in tipos_permitidos:
        raise ValueError(
            "Tipo de pessoa invalido."
        )

    if pessoa_id <= 0:
        raise ValueError(
            "ID deve ser maior que zero."
        )

    return f"{tipo}:{pessoa_id}"


def separar_identificador(identificador):

    tipo, pessoa_id = identificador.split(":")

    if tipo not in ("morador", "visitante"):
        raise ValueError(
            "Tipo de pessoa invalido."
        )

    return tipo, int(pessoa_id)
