import mysql.connector

def conectar_banco():
    meudb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="gcc272",
        database="consulta_net"
    )
    return meudb

def verificar_login(usuario, senha):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    query = "SELECT * FROM usuarios WHERE username = %s AND password = %s"
    cursor.execute(query, (usuario, senha))
    resultado = cursor.fetchone()
    cursor.close()
    conexao.close()
    return resultado
