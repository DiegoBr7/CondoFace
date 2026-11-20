
import getpass
from werkzeug.security import generate_password_hash
from conexao import conectar


def criar_administrador():

    conexao = None
    cursor = None

    try:
        print("\n=== CADASTRO DE ADMINISTRADOR ===")

        nome = input("Nome: ").strip()
        email = input("Email: ").strip().lower()

        senha = getpass.getpass("Senha: ")
        confirmar_senha = getpass.getpass(
            "Confirme a senha: "
        )

        if not nome or not email:
            print("Nome e email sao obrigatorios.")
            return

        if len(senha) < 12:
            print("A senha deve ter pelo menos 12 caracteres.")
            return

        if senha != confirmar_senha:
            print("As senhas nao coincidem.")
            return

        # Gera um hash seguro da senha.
        senha_hash = generate_password_hash(
            senha,
            method="scrypt"
        )

        conexao = conectar()
        cursor = conexao.cursor()

        sql = """
            INSERT INTO administradores (
                nome,
                email,
                senha_hash,
                ativo
            )
            VALUES (%s, %s, %s, TRUE)
        """

        cursor.execute(
            sql,
            (nome, email, senha_hash)
        )

        conexao.commit()

        print("\nAdministrador cadastrado com sucesso!")
        print("ID:", cursor.lastrowid)
        print("Nome:", nome)
        print("Email:", email)

    except Exception as erro:

        if conexao is not None:
            conexao.rollback()

        print("Erro ao cadastrar administrador:", erro)

    finally:

        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


if __name__ == "__main__":
    criar_administrador()
