
import cv2
import os
import pickle
import numpy as np

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

ARQUIVO_CLASSIFICADOR = os.path.join(
    BASE_DIR,
    "lbph_classifier.yml"
)

ARQUIVO_NOMES = os.path.join(
    BASE_DIR,
    "face_names.pickle"
)

LARGURA_FACE = 90
ALTURA_FACE = 120

MIN_FOTOS = 30


# ==========================================
# TREINAR MODELO
# ==========================================

def treinar():

    imagens = []
    identificadores = []

    mapa_pessoas = {}

    proximo_id = 1

    categorias = {
        "moradores": "morador",
        "visitantes": "visitante"
    }

    for pasta_categoria, tipo in categorias.items():

        caminho_categoria = os.path.join(
            PASTA_FACES,
            pasta_categoria
        )

        if not os.path.isdir(caminho_categoria):
            continue

        for pasta_id in sorted(
            os.listdir(caminho_categoria),
            key=lambda x: int(x) if x.isdigit() else float("inf")
        ):

            caminho_pessoa = os.path.join(
                caminho_categoria,
                pasta_id
            )

            if not os.path.isdir(caminho_pessoa):
                continue

            if not pasta_id.isdigit():
                print(
                    "Pasta ignorada:",
                    caminho_pessoa
                )
                continue

            pessoa_id = int(pasta_id)

            if pessoa_id <= 0:
                continue

            identificador = criar_identificador(
                tipo,
                pessoa_id
            )

            fotos_pessoa = []

            for arquivo in sorted(
                os.listdir(caminho_pessoa)
            ):

                if not arquivo.lower().endswith(
                    (".jpg", ".jpeg", ".png")
                ):
                    continue

                caminho_imagem = os.path.join(
                    caminho_pessoa,
                    arquivo
                )

                imagem = cv2.imread(
                    caminho_imagem,
                    cv2.IMREAD_GRAYSCALE
                )

                if imagem is None:
                    print(
                        "Imagem invalida:",
                        caminho_imagem
                    )
                    continue

                imagem = cv2.resize(
                    imagem,
                    (LARGURA_FACE, ALTURA_FACE)
                )

                fotos_pessoa.append(imagem)

            if len(fotos_pessoa) < MIN_FOTOS:

                print(
                    f"{identificador} ignorado: "
                    f"apenas {len(fotos_pessoa)} fotos."
                )

                continue

            mapa_pessoas[proximo_id] = identificador

            for imagem in fotos_pessoa:

                imagens.append(imagem)
                identificadores.append(proximo_id)

            print(
                f"{identificador}: "
                f"{len(fotos_pessoa)} imagens."
            )

            proximo_id += 1

    if not imagens:

        print(
            "Nenhuma pessoa com imagens "
            "suficientes para treinamento."
        )
        return

    # if len(mapa_pessoas) < 2:

    #     print(
    #         "Treinamento interrompido: "
    #         "cadastre pelo menos duas pessoas "
    #         "para o teste de reconhecimento."
    #     )
    #     return

    if not hasattr(cv2, "face"):

        print(
            "OpenCV sem modulo face. "
            "Verifique opencv-contrib-python."
        )
        return

    reconhecedor = cv2.face.LBPHFaceRecognizer_create()

    reconhecedor.train(
        imagens,
        np.array(
            identificadores,
            dtype=np.int32
        )
    )

    # Salvar em arquivos temporarios para
    # preservar os anteriores em caso de falha.
    classificador_temp = (
        ARQUIVO_CLASSIFICADOR + ".tmp.yml"
    )

    nomes_temp = (
        ARQUIVO_NOMES + ".tmp"
    )

    reconhecedor.write(classificador_temp)

    with open(nomes_temp, "wb") as arquivo:
        pickle.dump(mapa_pessoas, arquivo)

    os.replace(
        classificador_temp,
        ARQUIVO_CLASSIFICADOR
    )

    os.replace(
        nomes_temp,
        ARQUIVO_NOMES
    )

    print("\n================================")
    print("TREINAMENTO CONCLUIDO")
    print("================================")

    print("Pessoas:", len(mapa_pessoas))
    print("Imagens:", len(imagens))

    print("\nIdentificadores:")

    for codigo, pessoa in mapa_pessoas.items():
        print(codigo, "->", pessoa)

    print(
        "\nModelo salvo em:",
        ARQUIVO_CLASSIFICADOR
    )


if __name__ == "__main__":
    treinar()
