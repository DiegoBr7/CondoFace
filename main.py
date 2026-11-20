
import cv2
import numpy as np
import os
import pickle
import time

from identidade import separar_identificador

from morador_repository import buscar_morador_por_id
from visitante_repository import buscar_visitante_por_id

from autorizacao_repository import buscar_autorizacao
from autorizacao_visitante_repository import (
    buscar_autorizacao_visitante
)

from historico_repository import registrar_historico


# ==========================================
# CONFIGURACOES
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ARQUIVO_PROTO = os.path.join(
    BASE_DIR,
    "deploy.prototxt.txt"
)

ARQUIVO_MODELO = os.path.join(
    BASE_DIR,
    "res10_300x300_ssd_iter_140000.caffemodel"
)

ARQUIVO_LBPH = os.path.join(
    BASE_DIR,
    "lbph_classifier.yml"
)

ARQUIVO_NOMES = os.path.join(
    BASE_DIR,
    "face_names.pickle"
)

THRESHOLD = 80
CONFIANCA_DETECCAO = 0.90

LARGURA_FACE = 90
ALTURA_FACE = 120

LARGURA_CAMERA = 1280
ALTURA_CAMERA = 720

INTERVALO_CONSULTA = 3
TEMPO_AUSENCIA = 3
FRAMES_CONFIRMACAO = 5

DEBUG = True


# ==========================================
# CARREGAR MODELOS
# ==========================================

def carregar_modelos():

    arquivos = [
        ARQUIVO_PROTO,
        ARQUIVO_MODELO,
        ARQUIVO_LBPH,
        ARQUIVO_NOMES
    ]

    for caminho in arquivos:

        if not os.path.isfile(caminho):
            raise FileNotFoundError(
                f"Arquivo nao encontrado: {caminho}"
            )

    if not hasattr(cv2, "face"):
        raise RuntimeError(
            "OpenCV sem modulo face. "
            "Instale opencv-contrib-python."
        )

    detector = cv2.dnn.readNetFromCaffe(
        ARQUIVO_PROTO,
        ARQUIVO_MODELO
    )

    reconhecedor = (
        cv2.face.LBPHFaceRecognizer_create()
    )

    reconhecedor.read(ARQUIVO_LBPH)

    with open(ARQUIVO_NOMES, "rb") as arquivo:
        mapa_pessoas = pickle.load(arquivo)

    if not isinstance(mapa_pessoas, dict):
        raise ValueError(
            "Formato invalido do face_names.pickle."
        )

    # O treinar.py atual salva:
    # {1: "morador:1", 2: "visitante:1"}

    for codigo, identidade in mapa_pessoas.items():

        if not isinstance(codigo, int):
            raise ValueError(
                "Codigo LBPH deve ser inteiro."
            )

        if not isinstance(identidade, str):
            raise ValueError(
                "Identidade deve ser texto."
            )

        separar_identificador(identidade)

    print("\n================================")
    print("MODELO FACIAL CARREGADO")
    print("================================")

    for codigo, identidade in mapa_pessoas.items():
        print(f"{codigo} -> {identidade}")

    return detector, reconhecedor, mapa_pessoas


# ==========================================
# DETECTAR ROSTOS
# ==========================================

def detectar_rostos(frame, detector):

    altura, largura = frame.shape[:2]

    blob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)),
        1.0,
        (300, 300),
        (104.0, 117.0, 123.0)
    )

    detector.setInput(blob)

    deteccoes = detector.forward()

    rostos = []

    for i in range(deteccoes.shape[2]):

        confianca = float(
            deteccoes[0, 0, i, 2]
        )

        if confianca < CONFIANCA_DETECCAO:
            continue

        caixa = (
            deteccoes[0, 0, i, 3:7]
            * np.array([
                largura,
                altura,
                largura,
                altura
            ])
        )

        x1, y1, x2, y2 = caixa.astype(int)

        x1 = max(0, min(x1, largura))
        y1 = max(0, min(y1, altura))
        x2 = max(0, min(x2, largura))
        y2 = max(0, min(y2, altura))

        if x2 <= x1 or y2 <= y1:
            continue

        rostos.append((x1, y1, x2, y2))

    return rostos


# ==========================================
# RECONHECER ROSTO
# ==========================================

def reconhecer_rosto(
    frame,
    detector,
    reconhecedor,
    mapa_pessoas
):

    rostos = detectar_rostos(
        frame,
        detector
    )

    if len(rostos) != 1:

        if len(rostos) > 1:

            cv2.putText(
                frame,
                "APENAS UMA PESSOA",
                (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        return frame, None, len(rostos) > 0

    x1, y1, x2, y2 = rostos[0]

    rosto = frame[y1:y2, x1:x2]

    if rosto.size == 0:
        return frame, None, True

    rosto = cv2.cvtColor(
        rosto,
        cv2.COLOR_BGR2GRAY
    )

    rosto = cv2.resize(
        rosto,
        (LARGURA_FACE, ALTURA_FACE)
    )

    codigo, distancia = reconhecedor.predict(
        rosto
    )
    
    print(
        f"\nCodigo: {codigo}"
        f"\nDistancia: {distancia:.2f}"
        f"\nIdentidade: {mapa_pessoas.get(codigo)}"
        f"\nThreshold: {THRESHOLD}"
        f"\nDentro do limite: {distancia <= THRESHOLD}"
)

    identidade_encontrada = mapa_pessoas.get(
        codigo
    )

    # Diagnostico no terminal.
    if DEBUG:

        print(
            f"Codigo LBPH: {codigo} | "
            f"Distancia: {distancia:.2f} | "
            f"Identidade: {identidade_encontrada}",
            end="\r",
            flush=True
        )

    identidade = None

    if (
        distancia <= THRESHOLD
        and identidade_encontrada is not None
    ):

        identidade = identidade_encontrada

    cor = (
        (0, 255, 0)
        if identidade is not None
        else (0, 0, 255)
    )

    texto = (
        f"{identidade} - {distancia:.2f}"
        if identidade is not None
        else f"Desconhecido - {distancia:.2f}"
    )

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        cor,
        2
    )

    cv2.putText(
        frame,
        texto,
        (x1, max(25, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        cor,
        2
    )

    return frame, identidade, True


# ==========================================
# CONSULTAR ACESSO NO MYSQL
# ==========================================

def consultar_acesso(identidade):

    tipo, pessoa_id = separar_identificador(
        identidade
    )

    if tipo == "morador":

        pessoa = buscar_morador_por_id(
            pessoa_id
        )

        if pessoa is None:
            return tipo, None, "MORADOR NAO LOCALIZADO"

        if not bool(pessoa["ativo"]):
            return tipo, pessoa, "CADASTRO INATIVO"

        if not bool(pessoa["biometria_cadastrada"]):
            return tipo, pessoa, "BIOMETRIA NAO CADASTRADA"

        autorizacao = buscar_autorizacao(
            pessoa_id
        )

        if autorizacao is None:
            return tipo, pessoa, "SEM AUTORIZACAO"

        if not bool(autorizacao["permitido"]):
            return tipo, pessoa, "ACESSO NEGADO"

        return tipo, pessoa, "ACESSO PERMITIDO"

    if tipo == "visitante":

        pessoa = buscar_visitante_por_id(
            pessoa_id
        )

        if pessoa is None:
            return tipo, None, "VISITANTE NAO LOCALIZADO"

        if not bool(pessoa["ativo"]):
            return tipo, pessoa, "CADASTRO INATIVO"

        if not bool(pessoa["biometria_cadastrada"]):
            return tipo, pessoa, "BIOMETRIA NAO CADASTRADA"

        autorizacao = buscar_autorizacao_visitante(
            pessoa_id
        )

        if autorizacao is None:
            return tipo, pessoa, "SEM AUTORIZACAO VALIDA"

        return tipo, pessoa, "ACESSO PERMITIDO"

    return None, None, "TIPO INVALIDO"


# ==========================================
# REGISTRAR HISTORICO MYSQL
# ==========================================

def salvar_historico(tipo, pessoa, status):

    if pessoa is None:
        return False

    resultado = (
        "PERMITIDO"
        if status == "ACESSO PERMITIDO"
        else "NEGADO"
    )

    if tipo == "morador":

        registrar_historico(
            morador_id=pessoa["id"],
            resultado=resultado,
            motivo=status
        )

    elif tipo == "visitante":

        registrar_historico(
            visitante_id=pessoa["id"],
            resultado=resultado,
            motivo=status
        )

    else:
        return False

    return True


# ==========================================
# EXIBIR INFORMACOES
# ==========================================

def exibir_informacoes(
    frame,
    identidade,
    tipo,
    pessoa,
    status
):

    if status is None:
        return frame

    cor_status = (
        (0, 255, 0)
        if status == "ACESSO PERMITIDO"
        else (0, 0, 255)
    )

    cv2.putText(
        frame,
        status,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        cor_status,
        2
    )

    if pessoa is not None:

        cv2.putText(
            frame,
            f"Nome: {pessoa['nome']}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        if tipo == "morador":

            bloco = pessoa.get("bloco", "-")
            apartamento = pessoa.get(
                "apartamento", "-"
            )

            informacao = (
                f"Bloco: {bloco} "
                f"Ap: {apartamento}"
            )

        elif tipo == "visitante":

            informacao = "Tipo: VISITANTE"

        else:
            informacao = "Tipo: DESCONHECIDO"

        cv2.putText(
            frame,
            informacao,
            (20, 115),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    return frame


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

def main():

    detector, reconhecedor, mapa_pessoas = (
        carregar_modelos()
    )

    camera = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW
    )

    if not camera.isOpened():
        raise RuntimeError(
            "Nao foi possivel abrir a webcam."
        )

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        LARGURA_CAMERA
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        ALTURA_CAMERA
    )

    ultima_identidade = None
    ultimo_tipo = None
    ultima_pessoa = None
    ultimo_status = None

    ultima_consulta = 0.0
    ultimo_rosto_visto = None

    tentativa_registrada = False

    candidato = None
    frames_candidato = 0

    print("\nCondoFace iniciado!")
    print("Pressione Q para sair.")
    print("Modo: demonstracao academica.")

    try:

        while True:

            sucesso, frame = camera.read()

            if not sucesso:
                print("Erro ao capturar imagem.")
                break

            (
                frame,
                identidade_detectada,
                rosto_presente
            ) = reconhecer_rosto(
                frame,
                detector,
                reconhecedor,
                mapa_pessoas
            )

            agora = time.monotonic()

            # ==================================
            # CONFIRMAR IDENTIDADE
            # ==================================

            if identidade_detectada is not None:

                if identidade_detectada == candidato:
                    frames_candidato += 1
                else:
                    candidato = identidade_detectada
                    frames_candidato = 1

            else:
                candidato = None
                frames_candidato = 0

            if rosto_presente:
                ultimo_rosto_visto = agora

            identidade_confirmada = None

            if (
                candidato is not None
                and frames_candidato >= FRAMES_CONFIRMACAO
            ):
                identidade_confirmada = candidato

            # ==================================
            # ENCERRAR TENTATIVA
            # ==================================

            if (
                ultimo_rosto_visto is not None
                and agora - ultimo_rosto_visto
                >= TEMPO_AUSENCIA
            ):

                ultima_identidade = None
                ultimo_tipo = None
                ultima_pessoa = None
                ultimo_status = None

                ultima_consulta = 0.0
                ultimo_rosto_visto = None

                tentativa_registrada = False
                candidato = None
                frames_candidato = 0

            # ==================================
            # CONSULTAR MYSQL
            # ==================================

            if identidade_confirmada is not None:

                if identidade_confirmada != ultima_identidade:

                    ultima_identidade = identidade_confirmada

                    ultimo_tipo = None
                    ultima_pessoa = None
                    ultimo_status = None

                    ultima_consulta = 0.0
                    tentativa_registrada = False

                    print(
                        "\nIdentidade confirmada:",
                        identidade_confirmada
                    )

                consultar = (
                    ultimo_status is None
                    or agora - ultima_consulta
                    >= INTERVALO_CONSULTA
                )

                if consultar:

                    ultima_consulta = agora
                    ultimo_status = "VERIFICANDO ACESSO"

                    try:

                        (
                            ultimo_tipo,
                            ultima_pessoa,
                            ultimo_status
                        ) = consultar_acesso(
                            identidade_confirmada
                        )

                        print(
                            "\nResultado MySQL:",
                            ultimo_status
                        )

                    except Exception as erro:

                        print(
                            "\nErro ao consultar MySQL:",
                            erro
                        )

                        ultimo_tipo = None
                        ultima_pessoa = None
                        ultimo_status = "ERRO NO MYSQL"

                    if (
                        not tentativa_registrada
                        and ultimo_status not in (
                            "ERRO NO MYSQL",
                            "VERIFICANDO ACESSO"
                        )
                    ):

                        try:

                            registrado = salvar_historico(
                                ultimo_tipo,
                                ultima_pessoa,
                                ultimo_status
                            )

                            tentativa_registrada = registrado

                            if registrado:
                                print(
                                    "\nHistorico registrado."
                                )

                        except Exception as erro:

                            print(
                                "\nErro ao registrar historico:",
                                erro
                            )

            # ==================================
            # EXIBIR STATUS
            # ==================================

            if (
                identidade_confirmada is not None
                and ultimo_status is not None
            ):

                frame = exibir_informacoes(
                    frame,
                    identidade_confirmada,
                    ultimo_tipo,
                    ultima_pessoa,
                    ultimo_status
                )

            cv2.putText(
                frame,
                "MODO DEMONSTRACAO",
                (20, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.imshow(
                "CondoFace - Controle de Acesso",
                frame
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:

        camera.release()
        cv2.destroyAllWindows()

        print("\nCondoFace finalizado.")



if __name__ == "__main__":
    main()
