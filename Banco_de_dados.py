import mysql.connector

def conectar_banco():
    conexao = mysql.connector.connect(
        host="localhost",
        user="seu_usuario",
        password="sua_senha",
        database="nome_do_banco"
    )
    return conexao

def verificar_login(usuario, senha):
    conexao = conectar_banco()
    cursor = conexao.cursor()
    query = "SELECT * FROM usuarios WHERE username = %s AND password = %s"
    cursor.execute(query, (usuario, senha))
    resultado = cursor.fetchone()
    cursor.close()
    conexao.close()
    return resultado

from flask import Flask, request, redirect, url_for

app = Flask(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        senha = request.form['password']
        if verificar_login(usuario, senha):
            return redirect(url_for('pagina_protegida'))
        else:
            return "Login falhou. Tente novamente."
    return '''
        <form method="post">
            Usuário: <input type="text" name="username"><br>
            Senha: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/pagina_protegida')
def pagina_protegida():
    return "Bem-vindo à página protegida!"

if __name__ == '__main__':
    app.run(debug=True)