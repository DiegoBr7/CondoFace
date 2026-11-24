import cv2
from pathlib import Path

from cadastrar import processar_imagem_web
from identidade import criar_identificador

from historico_repository import listar_historico

import os
import hmac
import secrets

from datetime import timedelta
from functools import wraps

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    session,
    abort
)

from werkzeug.security import check_password_hash

from conexao import conectar


# ==========================================
# CONFIGURACOES
# ==========================================

app = Flask(__name__)

chave_secreta = os.environ.get(
    "CONDOFACE_SECRET_KEY"
)

if not chave_secreta:
    raise RuntimeError(
        "Configure CONDOFACE_SECRET_KEY "
        "antes de iniciar o Flask."
    )

app.config.update(
    SECRET_KEY=chave_secreta,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    PERMANENT_SESSION_LIFETIME=timedelta(
        minutes=30
    )
)

# Em producao com HTTPS:
# SESSION_COOKIE_SECURE=True


# ==========================================
# CONSULTAR ADMINISTRADOR
# ==========================================

def buscar_administrador_por_email(email):

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        sql = """
            SELECT
                id,
                nome,
                email,
                senha_hash,
                ativo
            FROM administradores
            WHERE email = %s
            LIMIT 1
        """

        cursor.execute(sql, (email,))

        return cursor.fetchone()

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


def administrador_ativo(admin_id):

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM administradores
            WHERE id = %s AND ativo = TRUE
            LIMIT 1
            """,
            (admin_id,)
        )

        return cursor.fetchone() is not None

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


# ==========================================
# PROTEGER ROTAS
# ==========================================

def login_required(funcao):

    @wraps(funcao)
    def verificar_login(*args, **kwargs):

        admin_id = session.get("admin_id")

        if admin_id is None:

            if request.path.startswith("/api/"):
                return jsonify({
                    "erro": "Nao autenticado"
                }), 401

            return redirect(url_for("login"))

        try:
            ativo = administrador_ativo(admin_id)

        except Exception:
            app.logger.exception(
                "Erro ao verificar administrador"
            )

            return jsonify({
                "erro": "Erro interno"
            }), 503

        if not ativo:
            session.clear()

            if request.path.startswith("/api/"):
                return jsonify({
                    "erro": "Nao autenticado"
                }), 401

            return redirect(url_for("login"))

        return funcao(*args, **kwargs)

    return verificar_login


# ==========================================
# PROTECAO CSRF
# ==========================================

def gerar_csrf_token():

    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)

    return session["csrf_token"]


@app.context_processor
def disponibilizar_csrf():
    return {
        "csrf_token": gerar_csrf_token
    }


def validar_csrf():

    token_recebido = request.form.get(
        "csrf_token", ""
    )

    token_sessao = session.get(
        "csrf_token", ""
    )

    if not token_recebido or not token_sessao:
        abort(400)

    if not hmac.compare_digest(
        token_recebido,
        token_sessao
    ):
        abort(400)


# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        if session.get("admin_id") is not None:

            try:
                if administrador_ativo(
                    session["admin_id"]
                ):
                    return redirect(
                        url_for("dashboard")
                    )
            except Exception:
                app.logger.exception(
                    "Erro ao verificar sessao"
                )

            session.clear()

        return render_template("login.html")

    validar_csrf()

    email = request.form.get(
        "email", ""
    ).strip().lower()

    senha = request.form.get(
        "senha", ""
    )

    if not email or not senha:

        return render_template(
            "login.html",
            erro="Informe e-mail e senha."
        ), 400

    try:

        admin = buscar_administrador_por_email(
            email
        )

        if (
            admin is None
            or not bool(admin["ativo"])
            or not check_password_hash(
                admin["senha_hash"],
                senha
            )
        ):

            return render_template(
                "login.html",
                erro="E-mail ou senha incorretos."
            ), 401

        session.clear()

        session["admin_id"] = admin["id"]
        session["admin_nome"] = admin["nome"]

        session.permanent = True

        return redirect(
            url_for("dashboard")
        )

    except Exception:

        app.logger.exception(
            "Erro durante autenticacao"
        )

        return render_template(
            "login.html",
            erro="Erro interno. Tente novamente."
        ), 500


# ==========================================
# LOGOUT
# ==========================================

@app.route("/logout", methods=["POST"])
@login_required
def logout():

    validar_csrf()

    session.clear()

    return redirect(
        url_for("login")
    )


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
@login_required
def dashboard():

    return render_template(
        "dashboard.html",
        administrador=session.get("admin_nome")
    )


# ==========================================
# API - DASHBOARD
# ==========================================

@app.route("/api/dashboard", methods=["GET"])
@login_required
def dados_dashboard():

    conexao = None
    cursor = None

    try:

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT COUNT(*) AS total FROM moradores"
        )

        moradores = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM visitantes"
        )

        visitantes = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM historico_acessos
            WHERE resultado = 'PERMITIDO'
        """)

        permitidos = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM historico_acessos
            WHERE resultado = 'NEGADO'
        """)

        negados = cursor.fetchone()["total"]

        return jsonify({
            "moradores": moradores,
            "visitantes": visitantes,
            "acessos_permitidos": permitidos,
            "acessos_negados": negados
        }), 200

    except Exception:

        app.logger.exception(
            "Erro ao consultar dashboard"
        )

        return jsonify({
            "erro": "Erro interno ao consultar dados."
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


# ==========================================
# API - MORADORES
# ==========================================

@app.route("/api/moradores", methods=["GET"])
@login_required
def listar_moradores():

    conexao = None
    cursor = None

    try:

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        sql = """
            SELECT
                id,
                nome,
                bloco,
                apartamento,
                ativo,
                biometria_cadastrada
            FROM moradores
            WHERE excluido = FALSE
            ORDER BY nome
        """

        cursor.execute(sql)

        moradores = cursor.fetchall()

        return jsonify(moradores), 200

    except Exception:

        app.logger.exception(
            "Erro ao listar moradores"
        )

        return jsonify({
            "erro": "Erro interno ao consultar moradores."
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


# ==========================================
# API - VISITANTES
# ==========================================

@app.route("/api/visitantes", methods=["GET"])
@login_required
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
                ativo,
                biometria_cadastrada
            FROM visitantes
            WHERE excluido = FALSE
            ORDER BY nome
        """

        cursor.execute(sql)

        visitantes = cursor.fetchall()

        return jsonify(visitantes), 200

    except Exception:

        app.logger.exception(
            "Erro ao buscar visitantes"
        )

        return jsonify({
            "erro": "Erro interno ao consultar visitantes."
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


# ==========================================
# EXECUTAR
# ==========================================


# ==========================================
# API - CADASTRAR MORADOR
# ==========================================

@app.route("/api/moradores", methods=["POST"])
@login_required
def cadastrar_morador():

    # Protege contra requisicoes CSRF
    validar_csrf()

    conexao = None
    cursor = None

    try:

        nome = request.form.get("nome", "").strip()
        bloco = request.form.get("bloco", "").strip()
        apartamento = request.form.get(
            "apartamento", ""
        ).strip()

        # Validar campos obrigatorios
        if not nome or not bloco or not apartamento:

            return jsonify({
                "erro": "Preencha todos os campos."
            }), 400

        # Validar tamanho dos campos
        if (
            len(nome) > 150
            or len(bloco) > 20
            or len(apartamento) > 20
        ):

            return jsonify({
                "erro": "Um dos campos excedeu "
                        "o tamanho permitido."
            }), 400

        conexao = conectar()
        cursor = conexao.cursor()

        sql = """
            INSERT INTO moradores (
                nome,
                bloco,
                apartamento
            )
            VALUES (%s, %s, %s)
        """

        cursor.execute(
            sql,
            (nome, bloco, apartamento)
        )

        conexao.commit()

        return jsonify({
            "mensagem": "Morador cadastrado com sucesso!",
            "id": cursor.lastrowid
        }), 201

    except Exception:

        if conexao is not None:
            conexao.rollback()

        app.logger.exception(
            "Erro ao cadastrar morador"
        )

        return jsonify({
            "erro": "Erro interno ao cadastrar morador."
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()



# ==========================================
# API - EDITAR MORADOR
# ==========================================

@app.route("/api/moradores/<int:morador_id>", methods=["PUT"])
@login_required
def editar_morador(morador_id):

    validar_csrf()

    nome = request.form.get("nome", "").strip()
    bloco = request.form.get("bloco", "").strip()
    apartamento = request.form.get(
        "apartamento", ""
    ).strip()

    if not nome or not bloco or not apartamento:
        return jsonify({
            "erro": "Preencha todos os campos."
        }), 400

    if (
        len(nome) > 150
        or len(bloco) > 20
        or len(apartamento) > 20
    ):
        return jsonify({
            "erro": "Um dos campos excedeu o limite."
        }), 400

    conexao = None
    cursor = None

    try:

        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE moradores
            SET nome = %s,
                bloco = %s,
                apartamento = %s
            WHERE id = %s
            """,
            (nome, bloco, apartamento, morador_id)
        )

        linhas = cursor.rowcount

        if linhas == 0:
            cursor.execute(
                "SELECT id FROM moradores WHERE id = %s AND excluido = FALSE",
                (morador_id,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    "erro": "Morador não encontrado."
                }), 404

        conexao.commit()

        return jsonify({
            "mensagem": "Morador atualizado com sucesso!"
        }), 200

    except Exception:

        if conexao is not None:
            conexao.rollback()

        app.logger.exception("Erro ao editar morador")

        return jsonify({
            "erro": "Erro interno ao editar morador."
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


# ==========================================
# API - ALTERAR STATUS DO MORADOR
# ==========================================

@app.route(
    "/api/moradores/<int:morador_id>/status",
    methods=["PATCH"]
)
@login_required
def alterar_status_morador(morador_id):

    validar_csrf()

    ativo = request.form.get("ativo")

    if ativo not in ("0", "1"):
        return jsonify({
            "erro": "Status inválido."
        }), 400

    conexao = None
    cursor = None

    try:

        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE moradores
            SET ativo = %s
            WHERE id = %s
            AND excluido = FALSE
            """,
            (int(ativo), morador_id)
        )

        linhas = cursor.rowcount

        if linhas == 0:
            cursor.execute(
                "SELECT id FROM moradores WHERE id = %s",
                (morador_id,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    "erro": "Morador não encontrado."
                }), 404

        conexao.commit()

        return jsonify({
            "mensagem": (
                "Morador ativado com sucesso!"
                if ativo == "1"
                else "Morador desativado com sucesso!"
            )
        }), 200

    except Exception:

        if conexao is not None:
            conexao.rollback()

        app.logger.exception(
            "Erro ao alterar status do morador"
        )

        return jsonify({
            "erro": "Erro interno ao alterar status."
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()



# ==========================================
# API - CADASTRAR VISITANTE
# ==========================================

@app.route("/api/visitantes", methods=["POST"])
@login_required
def cadastrar_visitante():

    validar_csrf()

    nome = request.form.get("nome", "").strip()
    documento = request.form.get("documento", "").strip()
    telefone = request.form.get("telefone", "").strip()

    # Validar campos
    if not nome:
        return jsonify({
            "erro": "Informe o nome do visitante."
        }), 400

    if (
        len(nome) > 150
        or len(documento) > 30
        or len(telefone) > 20
    ):
        return jsonify({
            "erro": "Um dos campos excedeu o limite permitido."
        }), 400

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        sql = """
            INSERT INTO visitantes (
                nome,
                documento,
                telefone,
                biometria_cadastrada,
                ativo
            )
            VALUES (%s, %s, %s, 0, 1)
        """

        cursor.execute(
            sql,
            (
                nome,
                documento or None,
                telefone or None
            )
        )

        visitante_id = cursor.lastrowid
        conexao.commit()

        return jsonify({
            "mensagem": "Visitante cadastrado com sucesso!",
            "id": visitante_id
        }), 201

    except Exception:
        if conexao is not None:
            conexao.rollback()

        app.logger.exception(
            "Erro ao cadastrar visitante"
        )

        return jsonify({
            "erro": "Erro interno ao cadastrar visitante."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


# ==========================================
# API - EDITAR VISITANTE
# ==========================================

@app.route(
    "/api/visitantes/<int:visitante_id>",
    methods=["PUT"]
)
@login_required
def editar_visitante(visitante_id):

    validar_csrf()

    nome = request.form.get("nome", "").strip()
    documento = request.form.get("documento", "").strip()
    telefone = request.form.get("telefone", "").strip()

    if not nome:
        return jsonify({
            "erro": "Informe o nome do visitante."
        }), 400

    if (
        len(nome) > 150
        or len(documento) > 30
        or len(telefone) > 20
    ):
        return jsonify({
            "erro": "Um dos campos excedeu o limite permitido."
        }), 400

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE visitantes
            SET nome = %s,
                documento = %s,
                telefone = %s
            WHERE id = %s
            """,
            (
                nome,
                documento or None,
                telefone or None,
                visitante_id
            )
        )

        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT id FROM visitantes WHERE id = %s AND excluido = FALSE",
                (visitante_id,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    "erro": "Visitante não encontrado."
                }), 404

        conexao.commit()

        return jsonify({
            "mensagem": "Visitante atualizado com sucesso!"
        }), 200

    except Exception:
        if conexao is not None:
            conexao.rollback()

        app.logger.exception("Erro ao editar visitante")

        return jsonify({
            "erro": "Erro interno ao editar visitante."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


# ==========================================
# API - ATIVAR / DESATIVAR VISITANTE
# ==========================================

@app.route(
    "/api/visitantes/<int:visitante_id>/status",
    methods=["PATCH"]
)
@login_required
def alterar_status_visitante(visitante_id):

    validar_csrf()

    ativo = request.form.get("ativo")

    if ativo not in ("0", "1"):
        return jsonify({
            "erro": "Status inválido."
        }), 400

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE visitantes
            SET ativo = %s
            WHERE id = %s
            AND excluido = FALSE
            """,
            (int(ativo), visitante_id)
        )

        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT id FROM visitantes WHERE id = %s",
                (visitante_id,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    "erro": "Visitante não encontrado."
                }), 404

        conexao.commit()

        return jsonify({
            "mensagem": (
                "Visitante ativado com sucesso!"
                if ativo == "1"
                else "Visitante desativado com sucesso!"
            )
        }), 200

    except Exception:
        if conexao is not None:
            conexao.rollback()

        app.logger.exception(
            "Erro ao alterar status do visitante"
        )

        return jsonify({
            "erro": "Erro interno ao alterar status."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()


# ==========================================
# CADASTRO FACIAL - CONFIGURACOES
# ==========================================

PASTA_BIOMETRIA = (
    Path(__file__).resolve().parent / "banco_faces"
)

MAX_TAMANHO_IMAGEM = 5 * 1024 * 1024  # 5 MB
MAX_FOTOS_BIOMETRIA = 30


# ==========================================
# CADASTRO FACIAL - RECEBER IMAGEM
# ==========================================

@app.route("/api/biometria/cadastrar", methods=["POST"])
@login_required
def cadastrar_biometria():

    validar_csrf()

    tipo = request.form.get("tipo", "").strip()
    pessoa_id_texto = request.form.get(
        "pessoa_id", ""
    ).strip()

    if tipo not in ("morador", "visitante"):
        return jsonify({
            "erro": "Tipo de pessoa inválido."
        }), 400

    try:
        pessoa_id = int(pessoa_id_texto)

        if pessoa_id <= 0:
            raise ValueError()

    except ValueError:
        return jsonify({
            "erro": "ID da pessoa inválido."
        }), 400

    imagem = request.files.get("imagem")

    if imagem is None:
        return jsonify({
            "erro": "Nenhuma imagem enviada."
        }), 400

    # Limita o tamanho recebido antes de processar
    if request.content_length is not None:
        if request.content_length > MAX_TAMANHO_IMAGEM:
            return jsonify({
                "erro": "Imagem excede o limite de 5 MB."
            }), 413

    imagem_bytes = imagem.read(
        MAX_TAMANHO_IMAGEM + 1
    )

    if len(imagem_bytes) > MAX_TAMANHO_IMAGEM:
        return jsonify({
            "erro": "Imagem excede o limite de 5 MB."
        }), 413

    tabela = (
        "moradores"
        if tipo == "morador"
        else "visitantes"
    )

    conexao = None
    cursor = None

    try:
        # ==================================
        # CONSULTAR PESSOA NO MYSQL
        # ==================================

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)

        # O nome da tabela é definido por uma
        # lista fechada, nunca pelo usuário.
        cursor.execute(
            f"""
            SELECT id, nome, ativo
            FROM {tabela}
            WHERE id = %s
            LIMIT 1
            """,
            (pessoa_id,)
        )

        pessoa = cursor.fetchone()

        if pessoa is None:
            return jsonify({
                "erro": "Pessoa não encontrada."
            }), 404

        if not bool(pessoa["ativo"]):
            return jsonify({
                "erro": "Cadastro inativo."
            }), 403

        # ==================================
        # PROCESSAR ROSTO COM OPENCV
        # ==================================

        try:
            rosto = processar_imagem_web(
                imagem_bytes
            )

        except ValueError as erro:
            return jsonify({
                "erro": str(erro)
            }), 400

        # ==================================
        # DEFINIR DIRETORIO
        # ==================================

        identificador = criar_identificador(
            tipo,
            pessoa_id
        )

        pasta_pessoa = (
            PASTA_BIOMETRIA
            / tabela
            / str(pessoa_id)
        )

        pasta_pessoa.mkdir(
            parents=True,
            exist_ok=True
        )

        # ==================================
        # CONTAR IMAGENS EXISTENTES
        # ==================================

        fotos_existentes = [
            arquivo
            for arquivo in pasta_pessoa.iterdir()
            if arquivo.is_file()
            and arquivo.suffix.lower() in (
                ".jpg", ".jpeg", ".png"
            )
        ]

        quantidade = len(fotos_existentes)

        if quantidade >= MAX_FOTOS_BIOMETRIA:
            return jsonify({
                "erro": (
                    "Esta pessoa já possui "
                    "30 imagens cadastradas."
                )
            }), 409

        # Evita sobrescrever imagens antigas.
        proximo_numero = 1

        while any(
            (pasta_pessoa / f"rosto_{proximo_numero:03d}{ext}").exists()
            for ext in (".jpg", ".jpeg", ".png")
                ):
            proximo_numero += 1

        caminho_imagem = (
            pasta_pessoa
            / f"rosto_{proximo_numero:03d}.jpg"
        )

        # ==================================
        # SALVAR IMAGEM PROCESSADA
        # ==================================

        salvou = cv2.imwrite(
            str(caminho_imagem),
            rosto
        )

        if not salvou:
            raise RuntimeError(
                "Falha ao salvar imagem facial."
            )

        quantidade += 1

        return jsonify({
            "mensagem": "Imagem facial cadastrada.",
            "identificador": identificador,
            "nome": pessoa["nome"],
            "quantidade": quantidade,
            "total": MAX_FOTOS_BIOMETRIA,
            "captura_concluida": (
                quantidade == MAX_FOTOS_BIOMETRIA
            )
        }), 201

    except Exception:
        app.logger.exception(
            "Erro no cadastro facial"
        )

        return jsonify({
            "erro": (
                "Erro interno ao cadastrar "
                "a imagem facial."
            )
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()



@app.route("/api/historico", methods=["GET"])
@login_required
def consultar_historico():
    try:
        historico = listar_historico()

        return jsonify(historico), 200

    except Exception:
        app.logger.exception(
            "Erro ao consultar historico"
        )

        return jsonify({
            "erro": "Erro ao consultar histórico"
        }), 500



# ==========================================
# API - EXCLUIR MORADOR
# ==========================================

@app.route("/api/moradores/<int:morador_id>", methods=["DELETE"])
@login_required
def excluir_morador(morador_id):

    validar_csrf()

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute("""
            UPDATE moradores
            SET ativo = FALSE,
                excluido = TRUE,
                biometria_cadastrada = FALSE
            WHERE id = %s
              AND excluido = FALSE
        """, (morador_id,))

        if cursor.rowcount == 0:
            return jsonify({
                "erro": "Morador não encontrado ou já excluído."
            }), 404

        cursor.execute("""
            UPDATE autorizacoes_visitantes
            SET permitido = FALSE
            WHERE morador_id = %s
        """, (morador_id,))

        conexao.commit()

        return jsonify({
            "mensagem": "Morador excluído com sucesso!"
        }), 200

    except Exception:

        if conexao is not None:
            conexao.rollback()

        app.logger.exception("Erro ao excluir morador")

        return jsonify({
            "erro": "Erro ao excluir morador."
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()
            

# ==========================================
# API - EXCLUIR MORADOR
# ==========================================

# ==========================================
# API - EXCLUIR VISITANTE
# ==========================================

@app.route("/api/visitantes/<int:visitante_id>", methods=["DELETE"])
@login_required
def excluir_visitante(visitante_id):

    validar_csrf()

    conexao = None
    cursor = None

    try:
        conexao = conectar()
        cursor = conexao.cursor()

        cursor.execute("""
            UPDATE visitantes
            SET ativo = FALSE,
                excluido = TRUE,
                biometria_cadastrada = FALSE
            WHERE id = %s
              AND excluido = FALSE
        """, (visitante_id,))

        if cursor.rowcount == 0:
            return jsonify({
                "erro": "Visitante não encontrado ou já excluído."
            }), 404

        cursor.execute("""
            UPDATE autorizacoes_visitantes
            SET permitido = FALSE
            WHERE visitante_id = %s
        """, (visitante_id,))

        conexao.commit()

        return jsonify({
            "mensagem": "Visitante excluído com sucesso!"
        }), 200

    except Exception:

        if conexao is not None:
            conexao.rollback()

        app.logger.exception("Erro ao excluir visitante")

        return jsonify({
            "erro": "Erro ao excluir visitante."
        }), 500

    finally:

        if cursor is not None:
            cursor.close()

        if conexao is not None:
            conexao.close()
            
            
if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
