
from conexao import conectar



def registrar_historico(
    resultado,
    motivo,
    morador_id=None,
    visitante_id=None
):
    if (morador_id is None) == (visitante_id is None):
        raise ValueError(
            "Informe apenas morador_id ou visitante_id."
        )

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        sql = """
            INSERT INTO historico_acessos (
                morador_id,
                visitante_id,
                resultado,
                motivo
            )
            VALUES (%s, %s, %s, %s)
        """

        valores = (
            morador_id,
            visitante_id,
            resultado,
            motivo
        )

        cursor.execute(sql, valores)
        conexao.commit()

        print("Histórico registrado com sucesso!")

    except Exception:
        if conexao is not None:
            conexao.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


def listar_historico():
    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        sql = """
            SELECT
                h.id,
                h.morador_id,
                h.visitante_id,
                h.data_hora,
                h.resultado,
                h.motivo,

                CASE
                    WHEN h.visitante_id IS NOT NULL
                        THEN 'Visitante'
                    WHEN h.morador_id IS NOT NULL
                        THEN 'Morador'
                    ELSE 'Desconhecido'
                END AS tipo_pessoa,

                CASE
                    WHEN h.visitante_id IS NOT NULL
                        THEN COALESCE(v.nome, 'Não encontrado')
                    WHEN h.morador_id IS NOT NULL
                        THEN COALESCE(m.nome, 'Não encontrado')
                    ELSE 'Desconhecido'
                END AS nome_pessoa

            FROM historico_acessos h

            LEFT JOIN moradores m
                ON h.morador_id = m.id

            LEFT JOIN visitantes v
                ON h.visitante_id = v.id

            ORDER BY h.data_hora DESC, h.id DESC

            LIMIT 50
        """

        cursor.execute(sql)

        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()
