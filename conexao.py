import mysql.connector

def conectar():
    conexao = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234567",
        database="condoface"
    )

    return conexao