
from conexao import conectar


# ==========================================
# CADASTRAR AUTORIZACAO
# ==========================================

def cadastrar_autorizacao(
    visitante_id,
    morador_id,
    inicio_validade,
    fim_validade,
    motivo
):

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        sql = """
            INSERT INTO autorizacoes_visitantes (
                visitante_id,
                morador_id,
                inicio_validade,
                fim_validade,
                permitido,
                motivo
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        valores = (
            visitante_id,
            morador_id,
            inicio_validade,
            fim_validade,
            True,
            motivo
        )

        cursor.execute(sql, valores)
        conexao.commit()

        return cursor.lastrowid

    except Exception:
        if conexao is not None:
            conexao.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


# ==========================================
# CONSULTAR AUTORIZACAO ATUAL
# ==========================================

def buscar_autorizacao_visitante(visitante_id):

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        sql = """
            SELECT
                av.id,
                av.visitante_id,
                av.morador_id,
                av.inicio_validade,
                av.fim_validade,
                av.permitido,
                av.motivo
            FROM autorizacoes_visitantes av
            INNER JOIN visitantes v
                ON v.id = av.visitante_id
            INNER JOIN moradores m
                ON m.id = av.morador_id
            WHERE av.visitante_id = %s
              AND av.permitido = TRUE
              AND v.ativo = TRUE
              AND m.ativo = TRUE
              AND NOW() BETWEEN
                  av.inicio_validade
                  AND av.fim_validade
            ORDER BY av.id DESC
            LIMIT 1
        """

        cursor.execute(sql, (visitante_id,))

        return cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()
