from flask import Flask, render_template, redirect, request, flash, send_from_directory, session
import json
import ast
import os
import mysql.connector
import random
import string

#inicia Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gabdan2004'

#variável global para verificar se o usuário está logado
logado = False

#função senha aleatória
def gerar_senha_aleatoria(tamanho=8):
    caracteres = string.ascii_letters + string.digits
    senha = ''.join(random.choice(caracteres) for i in range(tamanho))
    return senha

#função para obter informações do usuário
def obter_informacoes_usuario(email):
    #Conecta ao banco de dados MySQL
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        cursor = conexao_bd.cursor()
        cursor.execute('SELECT emailUsuario, nomeUsuario, sexoUsuario, idadeUsuario FROM usuario WHERE emailUsuario = %s', (email,))
        usuario = cursor.fetchone()
        cursor.close()
        conexao_bd.close()
        if usuario:
            return {
                'email': usuario[0],
                'nome': usuario[1],
                'sexo': usuario[2],
                'idade': usuario[3]
            }
    return None

#rota página inicial
@app.route('/')
def home():
    global logado
    logado = False
    return render_template('login.html')

#rota página de administrador ******************************
@app.route('/adm')
def adm():
    if logado:
        with open('usuarios.json') as usuariosTemp:
            usuarios = json.load(usuariosTemp)  # carrega dados dos usuários do JSON
        return render_template("administrador.html", usuarios=usuarios)  
    else:
        return redirect('/')  

#rota página download
@app.route('/pag_download')
def pag_download():
    if logado:
        arquivo = []
        for documento in os.listdir('arquivos'):
            arquivo.append(documento)  #add os nomes dos arquivos na lista
        return render_template("pag_download.html", arquivos=arquivo)  
    else:
        return redirect('/')  

#rota página tela usuário
@app.route('/tela_usuario')
def tela_usuario():
    if logado:
        email_do_usuario_logado = session.get('email')
        if email_do_usuario_logado:
            usuario = obter_informacoes_usuario(email_do_usuario_logado)
            if usuario:
                return render_template('tela_usuario.html', usuario=usuario)
        flash('Erro ao obter informações do usuário')
        return redirect('/')
    else:
        return redirect('/')

#rota login
@app.route('/login', methods=['POST'])
def login():
    global logado

    email = request.form.get('email')
    senha = request.form.get('senha')

    #conecta banco de dados MySQL
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    cont = 0
    if conexao_bd.is_connected():
        print('conectado')
        cursor = conexao_bd.cursor()  #cria um cursor para executar comandos SQL
        cursor.execute('SELECT * FROM usuario;')
        usuariosBD = cursor.fetchall()  #obtém todos os usuários do banco de dados

        for usuario in usuariosBD:
            cont += 1
            usuarioNome = str(usuario[1])
            usuarioSenha = str(usuario[2])

            if email == 'adm' and senha == '000':  #administrador
                logado = True
                session['email'] = email
                return redirect("/adm")
            
            if usuarioNome == email and usuarioSenha == senha:  #verifica se dados são válidas
                logado = True
                session['email'] = email
                return redirect('/tela_usuario')
            
            if cont >= len(usuariosBD):
                flash('USUARIO INVALIDO')
                return redirect("/")
    else:
        return redirect('/')  #redireciona para a página inicial se não conseguir conectar ao banco de dados

#rota cadastro
@app.route('/cadastrarUsuario', methods=['POST'])
def cadastrarUsuario():
    global logado
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    idade = request.form.get('idade')
    sexo = request.form.get('sexo')

    #conecta ao banco de dados MySQL
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        cursor = conexao_bd.cursor()
        cursor.execute('INSERT INTO usuario (nomeUsuario, emailUsuario, senhaUsuario, idadeUsuario, sexoUsuario) VALUES (%s, %s, %s, %s, %s)', (nome, email, senha, idade, sexo))
        conexao_bd.commit()
        cursor.close()
        conexao_bd.close()
        flash(f'{email} cadastrado com sucesso')
    else:
        flash('Erro ao conectar ao banco de dados')

    return redirect('/')

#rota excluir usuário **************
@app.route('/excluirUsuario', methods=['POST'])
def excluirUsuario():
    global logado
    logado = True
    usuario = request.form.get('usuarioPexcluir')  
    usuarioDict = ast.literal_eval(usuario)  
    email = usuarioDict['emailUsuario']
    with open('usuarios.json') as usuariosTemp:
        usuariosJson = json.load(usuariosTemp)  
        for c in usuariosJson:
            if c == usuarioDict:
                usuariosJson.remove(usuarioDict)  
                with open('usuarios.json', 'w') as usuarioAexcluir:
                    json.dump(usuariosJson, usuarioAexcluir, indent=4)  

    flash(f'{email} Excluido')  
    return redirect('/adm')

#rota upload arquivos
@app.route("/upload", methods=['POST'])
def upload():
    global logado
    logado = True

    arquivo = request.files.get('documento')  #obtém arquivo do formulário
    nome_arquivo = arquivo.filename.replace(" ","-")  #substitui espaços no nome do arquivo por hífens
    arquivo.save(os.path.join('arquivos/', nome_arquivo))  #salva o arquivo no diretório especificado

    flash('Arquivo salvo')
    return redirect('/adm')

#rota download arquivos
@app.route('/download', methods=['POST'])
def download():
    nomeArquivo = request.form.get('arquivosParaDownload')  #obtém o nome do arquivo a ser baixado do formulário

    return send_from_directory('arquivos', nomeArquivo, as_attachment=True)  #envia o arquivo para download

#rota página cadastro
@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

#rota página esqueci senha
@app.route('/esqueci_senha')
def esqueci_senha():
    return render_template('esqueci_senha.html')

#rota resetar senha
@app.route('/reset_senha', methods=['POST'])
def reset_senha():
    email = request.form.get('email')  #obtém email do formulário

    #conecta ao banco de dados MySQL
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        cursor = conexao_bd.cursor()
        nova_senha = gerar_senha_aleatoria()  #gera uma nova senha aleatória
        cursor.execute('UPDATE usuario SET senhaUsuario = %s WHERE emailUsuario = %s', (nova_senha, email))
        conexao_bd.commit()
        cursor.close()
        conexao_bd.close()
        flash(f'Nova senha enviada para {email}')
    else:
        flash('Erro ao conectar ao banco de dados')

    return redirect('/')

#rota tela medico
@app.route('/tela_medico')
def tela_medico():
    if logado:
        #conecta ao banco de dados MySQL
        conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
        if conexao_bd.is_connected():
            cursor = conexao_bd.cursor()
            cursor.execute('SELECT nomeMedicos, emailMedicos, especialidadeMedicos, disponibilidadeMedicos, idadeMedicos, statusMedicos FROM medicos')
            medicos = cursor.fetchall()
            cursor.close()
            conexao_bd.close()
            return render_template('tela_medico.html', medicos=medicos)
        else:
            flash('Erro ao conectar ao banco de dados')
            return redirect('/')
    else:
        return redirect('/')

#inicia Flask
if __name__ == "__main__":
    app.run(debug=True)