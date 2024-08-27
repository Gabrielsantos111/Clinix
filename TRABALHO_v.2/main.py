from flask import Flask, render_template, redirect, request, flash, send_from_directory
import json
import ast
import os
import mysql.connector
import random
import string

# Inicia Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gabdan2004'

# Variável global para verificar se o usuário está logado
logado = False

# Função para gerar uma senha aleatória
def gerar_senha_aleatoria(tamanho=8):
    caracteres = string.ascii_letters + string.digits
    senha = ''.join(random.choice(caracteres) for i in range(tamanho))
    return senha

# Rota para a página inicial
@app.route('/')
def home():
    global logado
    logado = False  # Define o estado de logado como False ao acessar a página inicial
    return render_template('login.html')  # Renderiza a página de login

# Rota para a página de administrador
@app.route('/adm')
def adm():
    if logado:  # Verifica se o usuário está logado
        with open('usuarios.json') as usuariosTemp:
            usuarios = json.load(usuariosTemp)  # Carrega os dados dos usuários do arquivo JSON
        return render_template("administrador.html", usuarios=usuarios)  # Renderiza a página de administrador com os dados dos usuários
    else:
        return redirect('/')  # Redireciona para a página inicial se não estiver logado

# Rota para a página de usuários
@app.route('/usuarios')
def usuarios():
    if logado:  # Verifica se o usuário está logado
        arquivo = []
        for documento in os.listdir('arquivos'):
            arquivo.append(documento)  # Adiciona os nomes dos arquivos à lista
        return render_template("usuarios.html", arquivos=arquivo)  # Renderiza a página de usuários com a lista de arquivos
    else:
        return redirect('/')  # Redireciona para a página inicial se não estiver logado

# Rota para o login
@app.route('/login', methods=['POST'])
def login():
    global logado

    email = request.form.get('email')  # Obtém o email do formulário
    senha = request.form.get('senha')  # Obtém a senha do formulário

    # Conecta ao banco de dados MySQL
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    cont = 0
    if conexao_bd.is_connected():
        print('conectado')
        cursor = conexao_bd.cursor()  # Cria um cursor para executar comandos SQL
        cursor.execute('SELECT * FROM usuario;')
        usuariosBD = cursor.fetchall()  # Obtém todos os usuários do banco de dados

        for usuario in usuariosBD:
            cont += 1
            usuarioNome = str(usuario[1])
            usuarioSenha = str(usuario[2])

            if email == 'adm' and senha == '000':  # Verifica se é o administrador
                logado = True
                return redirect("/adm")
            
            if usuarioNome == email and usuarioSenha == senha:  # Verifica se as credenciais são válidas
                logado = True
                return redirect('/usuarios')
            
            if cont >= len(usuariosBD):
                flash('USUARIO INVALIDO')  # Exibe mensagem de erro se as credenciais forem inválidas
                return redirect("/")
    else:
        return redirect('/')  # Redireciona para a página inicial se não conseguir conectar ao banco de dados

# Rota para cadastrar um novo usuário
@app.route('/cadastrarUsuario', methods=['POST'])
def cadastrarUsuario():
    global logado
    nome = request.form.get('nome')  # Obtém o nome do formulário
    email = request.form.get('email')  # Obtém o email do formulário
    senha = request.form.get('senha')  # Obtém a senha do formulário
    idade = request.form.get('idade')  # Obtém a idade do formulário
    sexo = request.form.get('sexo')  # Obtém o sexo do formulário

    # Conecta ao banco de dados MySQL
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        cursor = conexao_bd.cursor()
        cursor.execute('INSERT INTO usuario (nomeUsuario, emailUsuario, senhaUsuario, idadeUsuario, sexoUsuario) VALUES (%s, %s, %s, %s, %s)', (nome, email, senha, idade, sexo))
        conexao_bd.commit()
        cursor.close()
        conexao_bd.close()
        flash(f'{email} cadastrado com sucesso')  # Exibe mensagem de sucesso
    else:
        flash('Erro ao conectar ao banco de dados')  # Exibe mensagem de erro

    return redirect('/')

# Rota para excluir um usuário
@app.route('/excluirUsuario', methods=['POST'])
def excluirUsuario():
    global logado
    logado = True
    usuario = request.form.get('usuarioPexcluir')  # Obtém o usuário a ser excluído do formulário
    usuarioDict = ast.literal_eval(usuario)  # Converte a string do formulário em um dicionário
    email = usuarioDict['emailUsuario']
    with open('usuarios.json') as usuariosTemp:
        usuariosJson = json.load(usuariosTemp)  # Carrega os dados dos usuários do arquivo JSON
        for c in usuariosJson:
            if c == usuarioDict:
                usuariosJson.remove(usuarioDict)  # Remove o usuário da lista
                with open('usuarios.json', 'w') as usuarioAexcluir:
                    json.dump(usuariosJson, usuarioAexcluir, indent=4)  # Salva a lista atualizada de usuários no arquivo JSON

    flash(f'{email} Excluido')  # Exibe mensagem de sucesso
    return redirect('/adm')

# Rota para upload de arquivos
@app.route("/upload", methods=['POST'])
def upload():
    global logado
    logado = True

    arquivo = request.files.get('documento')  # Obtém o arquivo do formulário
    nome_arquivo = arquivo.filename.replace(" ","-")  # Substitui espaços no nome do arquivo por hífens
    arquivo.save(os.path.join('arquivos/', nome_arquivo))  # Salva o arquivo no diretório especificado

    flash('Arquivo salvo')  # Exibe mensagem de sucesso
    return redirect('/adm')

# Rota para download de arquivos
@app.route('/download', methods=['POST'])
def download():
    nomeArquivo = request.form.get('arquivosParaDownload')  # Obtém o nome do arquivo a ser baixado do formulário

    return send_from_directory('arquivos', nomeArquivo, as_attachment=True)  # Envia o arquivo para download

# Rota para a página de cadastro
@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

# Rota para a página de esqueci a senha
@app.route('/esqueci_senha')
def esqueci_senha():
    return render_template('esqueci_senha.html')

# Rota para resetar a senha
@app.route('/reset_senha', methods=['POST'])
def reset_senha():
    email = request.form.get('email')  # Obtém o email do formulário

    # Conecta ao banco de dados MySQL
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        cursor = conexao_bd.cursor()
        nova_senha = gerar_senha_aleatoria()  # Gera uma nova senha aleatória
        cursor.execute('UPDATE usuario SET senhaUsuario = %s WHERE emailUsuario = %s', (nova_senha, email))
        conexao_bd.commit()
        cursor.close()
        conexao_bd.close()
        flash(f'Nova senha enviada para {email}')  #mensagem de sucesso
    else:
        flash('Erro ao conectar ao banco de dados')  #mensagem de erro

    return redirect('/')

# inicia Flask
if __name__ == "__main__":
    app.run(debug=True)