
from conexao import conectar


def buscar_autorizacao(morador_id):

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        sql = """
            SELECT
                id,
                morador_id,
                permitido,
                motivo
            FROM autorizacoes
            WHERE morador_id = %s
            ORDER BY criado_em DESC, id DESC
            LIMIT 1
        """

        cursor.execute(sql, (morador_id,))

        autorizacao = cursor.fetchone()

        return autorizacao

    except Exception as erro:
        print("Erro ao consultar autorizacao:", erro)
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None and conexao.is_connected():
            conexao.close()
