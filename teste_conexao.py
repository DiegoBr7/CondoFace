from conexao import conectar

try:
    conexao = conectar()

    if conexao.is_connected():
        print("Conexão com MySQL realizada com sucesso!")

    cursor = conexao.cursor(dictionary=True)

    cursor.execute("SELECT * FROM moradores")

    moradores = cursor.fetchall()

    for morador in moradores:
        print(morador)

except Exception as erro:
    print("Erro ao conectar:", erro)

finally:
    if "cursor" in locals():
        cursor.close()

    if "conexao" in locals() and conexao.is_connected():
        conexao.close()