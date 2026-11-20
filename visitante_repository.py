
from conexao import conectar


# ==========================================
# CADASTRAR VISITANTE
# ==========================================

def cadastrar_visitante(nome, documento, telefone):

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        sql = """
            INSERT INTO visitantes
                (nome, documento, telefone)
            VALUES (%s, %s, %s)
        """

        valores = (
            nome,
            documento,
            telefone
        )

        cursor.execute(sql, valores)

        conexao.commit()

        visitante_id = cursor.lastrowid

        return visitante_id

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
# BUSCAR VISITANTE PELO ID
# ==========================================

def buscar_visitante_por_nome(nome):

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        sql = """
            SELECT
                id,
                nome,
                ativo,
                biometria_cadastrada
            FROM visitantes
            WHERE nome = %s
        """

        cursor.execute(sql, (nome,))

        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()

# ==========================================
# LISTAR VISITANTES
# ==========================================

def listar_visitantes():

    conexao = None
    cursor = None

    try:
        conexao = conectar()

        cursor = conexao.cursor(dictionary=True)

        sql = """
            SELECT
                id,
                nome,
                documento,
                telefone,
                biometria_cadastrada,
                ativo
            FROM visitantes
            ORDER BY nome
        """

        cursor.execute(sql)

        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()

# ==========================================
# BUSCAR VISITANTE PELO ID
# ==========================================

def buscar_visitante_por_id(visitante_id):

    conexao = None
    cursor = None

    try:
        conexao = conectar()

        cursor = conexao.cursor(
            dictionary=True
        )

        sql = """
            SELECT
                id,
                nome,
                documento,
                telefone,
                biometria_cadastrada,
                ativo
            FROM visitantes
            WHERE id = %s
        """

        cursor.execute(
            sql,
            (visitante_id,)
        )

        visitante = cursor.fetchone()

        return visitante

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()
