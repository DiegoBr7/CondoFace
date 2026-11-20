
import cv2
import os
import time
import numpy as np

from morador_repository import buscar_morador_por_id
from visitante_repository import buscar_visitante_por_id
from identidade import criar_identificador


# ==========================================
# CONFIGURACOES
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PASTA_FACES = os.path.join(
    BASE_DIR,
    "banco_faces"
)

ARQUIVO_PROTO = os.path.join(
    BASE_DIR,
    "deploy.prototxt.txt"
)

ARQUIVO_MODELO = os.path.join(
    BASE_DIR,
    "res10_300x300_ssd_iter_140000.caffemodel"
)

MAX_FOTOS = 30

INTERVALO = 0.5

CONFIANCA_MINIMA = 0.90

LARGURA_FACE = 90
ALTURA_FACE = 120

LARGURA_CAMERA = 1280
ALTURA_CAMERA = 720

TAMANHO_MINIMO_FACE = 35


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

        if confianca < CONFIANCA_MINIMA:
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

        if (
            x2 - x1 < TAMANHO_MINIMO_FACE
            or y2 - y1 < TAMANHO_MINIMO_FACE
        ):
            continue

        rostos.append(
            (x1, y1, x2, y2)
        )

    return rostos


# ==========================================
# PROCESSAR ROSTO
# ==========================================

def processar_rosto(frame, coordenadas):

    x1, y1, x2, y2 = coordenadas

    rosto = frame[y1:y2, x1:x2]

    if rosto.size == 0:
        return None

    rosto = cv2.cvtColor(
        rosto,
        cv2.COLOR_BGR2GRAY
    )

    rosto = cv2.resize(
        rosto,
        (LARGURA_FACE, ALTURA_FACE)
    )

    return rosto


# ==========================================
# ESCOLHER TIPO DE PESSOA
# ==========================================

def escolher_tipo():

    print("\n================================")
    print("       CONDOFACE")
    print("================================")

    print("1 - Cadastrar morador")
    print("2 - Cadastrar visitante")
    print("0 - Sair")

    opcao = input(
        "\nEscolha uma opcao: "
    ).strip()

    if opcao == "1":
        return "morador"

    if opcao == "2":
        return "visitante"

    if opcao == "0":
        return None

    print("Opcao invalida!")

    return None


# ==========================================
# CONSULTAR PESSOA NO MYSQL
# ==========================================

def consultar_pessoa(tipo, pessoa_id):

    if tipo == "morador":

        return buscar_morador_por_id(
            pessoa_id
        )

    if tipo == "visitante":

        return buscar_visitante_por_id(
            pessoa_id
        )

    return None


# ==========================================
# VERIFICAR CADASTRO
# ==========================================

def verificar_cadastro(tipo, pessoa_id):

    try:

        pessoa = consultar_pessoa(
            tipo,
            pessoa_id
        )

    except Exception as erro:

        print(
            "Erro ao consultar MySQL:",
            erro
        )

        return None

    if pessoa is None:

        print(
            "Pessoa nao encontrada no MySQL."
        )

        return None

    if not bool(pessoa["ativo"]):

        print(
            "Cadastro inativo. "
            "Nao e possivel capturar o rosto."
        )

        return None

    identificador = criar_identificador(
        tipo,
        pessoa_id
    )

    print("\n================================")
    print("PESSOA ENCONTRADA")
    print("================================")

    print("Nome:", pessoa["nome"])
    print("Tipo:", tipo)
    print("ID:", pessoa_id)
    print("Identificador:", identificador)

    return pessoa


# ==========================================
# DEFINIR PASTA DAS IMAGENS
# ==========================================

def obter_pasta_pessoa(tipo, pessoa_id):

    categoria = (
        "moradores"
        if tipo == "morador"
        else "visitantes"
    )

    return os.path.join(
        PASTA_FACES,
        categoria,
        str(pessoa_id)
    )


# ==========================================
# VERIFICAR IMAGENS EXISTENTES
# ==========================================

def verificar_imagens_existentes(pasta):

    if not os.path.isdir(pasta):
        return False

    imagens = [
        arquivo
        for arquivo in os.listdir(pasta)
        if arquivo.lower().endswith(
            (".jpg", ".jpeg", ".png")
        )
    ]

    if imagens:

        print(
            f"\nJa existem {len(imagens)} "
            "imagens cadastradas."
        )

        print(
            "Cadastro interrompido para "
            "evitar sobrescrever imagens."
        )

        return True

    return False


# ==========================================
# CAPTURAR IMAGENS
# ==========================================

def capturar_imagens(pasta, nome):

    detector = cv2.dnn.readNetFromCaffe(
        ARQUIVO_PROTO,
        ARQUIVO_MODELO
    )

    camera = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW
    )

    if not camera.isOpened():

        print(
            "Erro ao abrir webcam."
        )

        return 0

    camera.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        LARGURA_CAMERA
    )

    camera.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        ALTURA_CAMERA
    )

    contador = 0

    ultima_foto = 0

    print("\n================================")
    print("CAPTURA FACIAL")
    print("================================")

    print("Pessoa:", nome)

    print(
        "Mantenha apenas uma pessoa "
        "diante da webcam."
    )

    print(
        "Movimente levemente o rosto."
    )

    print(
        "Pressione Q para cancelar.\n"
    )

    try:

        while contador < MAX_FOTOS:

            sucesso, frame = camera.read()

            if not sucesso:

                print(
                    "Erro ao capturar imagem."
                )

                break

            rostos = detectar_rostos(
                frame,
                detector
            )

            if len(rostos) == 1:

                coordenadas = rostos[0]

                rosto = processar_rosto(
                    frame,
                    coordenadas
                )

                if rosto is not None:

                    x1, y1, x2, y2 = coordenadas

                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2
                    )

                    agora = time.monotonic()

                    if (
                        agora - ultima_foto
                        >= INTERVALO
                    ):

                        proximo = contador + 1

                        caminho = os.path.join(
                            pasta,
                            f"rosto_{proximo:03d}.jpg"
                        )

                        salvou = cv2.imwrite(
                            caminho,
                            rosto
                        )

                        if salvou:

                            contador = proximo

                            ultima_foto = agora

                            print(
                                f"Foto {contador}/"
                                f"{MAX_FOTOS} salva!"
                            )

            elif len(rostos) > 1:

                cv2.putText(
                    frame,
                    "APENAS UMA PESSOA",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            else:

                cv2.putText(
                    frame,
                    "ROSTO NAO DETECTADO",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            cv2.putText(
                frame,
                f"Fotos: {contador}/{MAX_FOTOS}",
                (20, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

            cv2.imshow(
                "CondoFace - Cadastro Facial",
                frame
            )

            tecla = cv2.waitKey(1) & 0xFF

            if tecla == ord("q"):

                print(
                    "Captura interrompida."
                )

                break

    finally:

        camera.release()

        cv2.destroyAllWindows()

    return contador


# ==========================================
# CADASTRAR PESSOA
# ==========================================

def cadastrar():

    tipo = escolher_tipo()

    if tipo is None:
        return

    try:

        pessoa_id = int(
            input(
                "Digite o ID da pessoa: "
            )
        )

    except ValueError:

        print("ID invalido!")

        return

    if pessoa_id <= 0:

        print(
            "O ID deve ser maior que zero."
        )

        return

    pessoa = verificar_cadastro(
        tipo,
        pessoa_id
    )

    if pessoa is None:
        return

    confirmar = input(
        "\nConfirma o cadastro facial? (s/n): "
    ).strip().lower()

    if confirmar != "s":

        print(
            "Cadastro cancelado."
        )

        return

    pasta_pessoa = obter_pasta_pessoa(
        tipo,
        pessoa_id
    )

    if verificar_imagens_existentes(
        pasta_pessoa
    ):
        return

    os.makedirs(
        pasta_pessoa,
        exist_ok=True
    )

    quantidade = capturar_imagens(
        pasta_pessoa,
        pessoa["nome"]
    )

    print("\n================================")
    print("RESULTADO DO CADASTRO")
    print("================================")

    print(
        "Nome:",
        pessoa["nome"]
    )

    print(
        "Tipo:",
        tipo
    )

    print(
        "Imagens capturadas:",
        quantidade
    )

    print(
        "Pasta:",
        pasta_pessoa
    )

    if quantidade == MAX_FOTOS:

        print(
            "\nCaptura facial concluida!"
        )

        print(
            "Proximo passo: treinar o modelo."
        )

    else:

        print(
            "\nCaptura incompleta."
        )

        print(
            "As imagens existentes foram "
            "preservadas."
        )

        print(
            "Complete o cadastro antes "
            "de realizar o treinamento."
        )


# ==========================================
# EXECUTAR
# ==========================================



def processar_imagem_web(imagem_bytes):
    """
    Recebe os bytes de uma imagem enviada
    pelo navegador e retorna o rosto
    processado em escala de cinza.
    """

    if not imagem_bytes:
        raise ValueError("Imagem não enviada.")

    imagem_array = np.frombuffer(
        imagem_bytes,
        dtype=np.uint8
    )

    frame = cv2.imdecode(
        imagem_array,
        cv2.IMREAD_COLOR
    )

    if frame is None:
        raise ValueError("Imagem inválida.")

    detector = cv2.dnn.readNetFromCaffe(
        ARQUIVO_PROTO,
        ARQUIVO_MODELO
    )

    rostos = detectar_rostos(
        frame,
        detector
    )

    if len(rostos) == 0:
        raise ValueError(
            "Nenhum rosto detectado."
        )

    if len(rostos) > 1:
        raise ValueError(
            "Mais de um rosto detectado."
        )

    rosto = processar_rosto(
        frame,
        rostos[0]
    )

    if rosto is None:
        raise ValueError(
            "Não foi possível processar o rosto."
        )

    return rosto


if __name__ == "__main__":

    cadastrar()
