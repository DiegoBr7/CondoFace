from conexao import conectar


def buscar_morador_por_nome(nome):
    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        sql = """
            SELECT id, nome, bloco, apartamento,
                   ativo, biometria_cadastrada
            FROM moradores
            WHERE nome = %s
        """

        cursor.execute(sql, (nome,))

        morador = cursor.fetchone()

        return morador

    except Exception as erro:
        print("Erro ao buscar morador:", erro)
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()
            

def buscar_morador_por_id(morador_id):
    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, nome, ativo, biometria_cadastrada
            FROM moradores
            WHERE id = %s
            """,
            (morador_id,)
        )

        return cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()