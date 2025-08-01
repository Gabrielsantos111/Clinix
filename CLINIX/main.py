from flask import Flask, render_template, redirect, request, flash, send_from_directory, session, url_for
import json
import ast
import os
import mysql.connector
import random
import string
from flask_mail import Mail, Message
from datetime import datetime, timedelta

#inicia Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gabdan2004'

# Configurações de e-mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Servidor SMTP (Gmail, por exemplo)
app.config['MAIL_PORT'] = 587  # Porta para envio seguro
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'clinix.projeto@gmail.com'  # Seu e-mail
app.config['MAIL_PASSWORD'] = 'adrszlubvsgzwivr '  # Sua senha ou app password
app.config['MAIL_DEFAULT_SENDER'] = ('Consulta Online', 'clinix.projeto@gmail.com')

# Inicializar Flask-Mail
mail = Mail(app)

#variável global para verificar se o usuário está logado
logado = False

from datetime import datetime

@app.template_filter('datetimeformat')
def datetimeformat(value):
    """
    Formata uma data no formato DD/MM/AAAA.
    """
    try:
        return datetime.strptime(value, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception as e:
        return value

#função para obter informações do usuário
def obter_informacoes_usuario(email):
    #Conecta ao banco de dados MySQL
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        cursor = conexao_bd.cursor()
        cursor.execute('SELECT emailUsuario, nomeUsuario, sexoUsuario, idadeUsuario, telefoneUsuario, enderecoUsuario FROM usuario WHERE emailUsuario = %s', (email,))
        usuario = cursor.fetchone()
        cursor.close()
        conexao_bd.close()
        if usuario:
            return {
                'email': usuario[0],
                'nome': usuario[1],
                'sexo': usuario[2],
                'idade': usuario[3],
                'telefone': usuario[4],
                'endereco': usuario[5]
            }
    return None

def obter_informacoes_medico(crm):
    # Conecta ao banco de dados MySQL
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        cursor = conexao_bd.cursor()
        cursor.execute('SELECT nomeMedicos, emailMedicos, idadeMedicos, statusMedicos, crmMedicos FROM medicos WHERE crmMedicos = %s', (crm,))
        medico = cursor.fetchone()
        cursor.close()
        conexao_bd.close()
        if medico:
            return {
                'nome': medico[0],
                'email': medico[1],
                'idade': medico[2],
                'status': medico[3],
                'crm': medico[4]
            }
    return None

#rota página inicial
@app.route('/')
def home():
    global logado
    logado = False
    return render_template('login.html')

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    global logado

    if request.method == 'GET':
        # Renderiza a página de login no método GET
        return render_template('login.html')

    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        # Conecta ao banco de dados MySQL
        conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
        if conexao_bd.is_connected():
            try:
                cursor = conexao_bd.cursor()
                cursor.execute('SELECT emailUsuario, senhaUsuario FROM usuario')
                usuariosBD = cursor.fetchall()

                # Verifica credenciais
                for usuario in usuariosBD:
                    usuarioNome, usuarioSenha = usuario

                    # Verifica se é o administrador
                    if email == 'adm' and senha == '000':
                        logado = True
                        session['email'] = email
                        return redirect("/adm")

                    # Verifica se o e-mail e a senha do usuário são válidos
                    if usuarioNome == email and usuarioSenha == senha:
                        logado = True
                        session['email'] = email
                        return redirect('/tela_usuario')

                flash('Usuário ou senha inválidos')
                return redirect('/login')  # Retorna à página de login com mensagem de erro
            except mysql.connector.Error as err:
                flash(f"Erro ao acessar banco de dados: {err}")
                return redirect('/login')
            finally:
                cursor.close()
                conexao_bd.close()

        flash("Erro ao conectar ao banco de dados")
        return redirect('/login')

#rota cadastro
@app.route('/cadastrarUsuario', methods=['POST'])
def cadastrarUsuario():
    global logado
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    idade = request.form.get('idade')
    sexo = request.form.get('sexo')
    telefone = request.form.get('telefone')
    endereco = request.form.get('endereco')

    # Validação do número de telefone
    if len(telefone) > 15:
        flash('Número de telefone muito longo')
        return redirect('/cadastro')

    #conecta ao banco de dados MySQL
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        cursor = conexao_bd.cursor()
        cursor.execute('INSERT INTO usuario (nomeUsuario, emailUsuario, senhaUsuario, idadeUsuario, sexoUsuario, telefoneUsuario, enderecoUsuario) VALUES (%s, %s, %s, %s, %s, %s, %s)', (nome, email, senha, idade, sexo, telefone, endereco))
        conexao_bd.commit()
        cursor.close()
        conexao_bd.close()
        flash(f'{email} cadastrado com sucesso')
    else:
        flash('Erro ao conectar ao banco de dados')

    return redirect('/')

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
@app.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'GET':
        return render_template('esqueci_senha.html')
    # Processar lógica de redefinição no método POST
    email_usuario = request.form.get('email')
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()

            # Verifica se o e-mail existe no banco de dados
            cursor.execute('SELECT idUsuario FROM usuario WHERE emailUsuario = %s', (email_usuario,))
            usuario = cursor.fetchone()

            if not usuario:
                flash("E-mail não encontrado.")
                return redirect('/login')

            id_usuario = usuario[0]

            # Gera um token único para redefinir senha
            from itsdangerous import URLSafeTimedSerializer
            s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
            token = s.dumps(email_usuario, salt='redefinir-senha')

            # Envia o e-mail com o link de redefinição
            link = f"http://127.0.0.1:5000/redefinir_senha/{token}"
            msg = Message("Redefinição de Senha", recipients=[email_usuario])
            msg.body = f'''
            Olá,

            Você solicitou a redefinição de sua senha. Clique no link abaixo para redefinir:

            {link}

            Se você não fez esta solicitação, ignore este e-mail.
            '''
            mail.send(msg)

            flash("E-mail de redefinição de senha enviado.")
            return redirect('/login')
        except mysql.connector.Error as err:
            flash(f"Erro ao processar solicitação: {err}")
            return redirect('/login')
        finally:
            cursor.close()
            conexao_bd.close()

#rota resetar senha
@app.route('/redefinir_senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadData
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    try:
        email_usuario = s.loads(token, salt='redefinir-senha', max_age=3600)  # 1 hora de validade
    except (SignatureExpired, BadData):
        flash("O link de redefinição expirou ou é inválido.")
        return redirect('/login')

    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
        if conexao_bd.is_connected():
            try:
                cursor = conexao_bd.cursor()
                cursor.execute('UPDATE usuario SET senhaUsuario = %s WHERE emailUsuario = %s', (nova_senha, email_usuario))
                conexao_bd.commit()

                flash("Senha redefinida com sucesso!")
                return redirect('/login')
            except mysql.connector.Error as err:
                flash(f"Erro ao redefinir senha: {err}")
                return redirect('/login')
            finally:
                cursor.close()
                conexao_bd.close()

    return render_template('redefinir_senha.html', email=email_usuario)

@app.route('/tela_medico')
def tela_medico():
    if logado:
        conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
        if conexao_bd.is_connected():
            try:
                cursor = conexao_bd.cursor()
                cursor.execute('''
                    SELECT m.idMedicos, m.nomeMedicos, m.emailMedicos, m.idadeMedicos, m.statusMedicos, GROUP_CONCAT(e.nomeEspecialidade SEPARATOR ', ')
                    FROM medicos m
                    JOIN medicos_especialidades me ON m.idMedicos = me.idMedico
                    JOIN especialidades e ON me.idEspecialidade = e.idEspecialidade
                    GROUP BY m.idMedicos, m.nomeMedicos, m.emailMedicos, m.idadeMedicos, m.statusMedicos
                ''')
                medicos = cursor.fetchall()
                cursor.close()
                conexao_bd.close()
                return render_template('tela_medico.html', medicos=medicos)
            except mysql.connector.Error as err:
                flash(f"Erro ao carregar médicos: {err}")
                return redirect('/')
    else:
        flash('Por favor, faça login primeiro.')
        return redirect('/')

@app.route('/atualizar_cadastro')
def atualizar_cadastro():
    if logado:
        email_do_usuario_logado = session.get('email')
        if email_do_usuario_logado:
            usuario = obter_informacoes_usuario(email_do_usuario_logado)
            if usuario:
                return render_template('atualizar_cadastro.html', usuario=usuario)
        flash('Erro ao obter informações do usuário')
        return redirect('/')
    else:
        return redirect('/')

@app.route('/atualizar_cadastro', methods=['POST'])
def processar_atualizacao():
    if logado:
        email = session.get('email')
        nome = request.form.get('nome')
        senha = request.form.get('senha')
        idade = request.form.get('idade')
        sexo = request.form.get('sexo')
        telefone = request.form.get('telefone')
        endereco = request.form.get('endereco')

        if not nome or not senha or not idade or not sexo or not telefone or not endereco:
            flash('Todos os campos são obrigatórios')
            return redirect('/atualizar_cadastro')

        # Conecta ao banco de dados MySQL
        conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
        if conexao_bd.is_connected():
            cursor = conexao_bd.cursor()
            cursor.execute('UPDATE usuario SET nomeUsuario = %s, senhaUsuario = %s, idadeUsuario = %s, sexoUsuario = %s, telefoneUsuario = %s, enderecoUsuario = %s WHERE emailUsuario = %s', (nome, senha, idade, sexo, telefone, endereco, email))
            conexao_bd.commit()
            cursor.close()
            conexao_bd.close()
            flash('Cadastro atualizado com sucesso')
            return redirect('/tela_usuario')
        else:
            flash('Erro ao conectar ao banco de dados')
            return redirect('/atualizar_cadastro')
    else:
        return redirect('/')
    
@app.route('/confirmar_exclusao')
def confirmar_exclusao():
    if logado:
        return render_template('confirmar_exclusao.html')
    else:
        return redirect('/')

@app.route('/excluir_cadastro', methods=['POST'])
def excluir_cadastro():
    if logado:
        email = session.get('email')
        # Conecta ao banco de dados MySQL
        conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
        if conexao_bd.is_connected():
            cursor = conexao_bd.cursor()
            cursor.execute('DELETE FROM usuario WHERE emailUsuario = %s', (email,))
            conexao_bd.commit()
            cursor.close()
            conexao_bd.close()
            session.pop('email', None)
            flash('Cadastro excluído com sucesso')
            return redirect('/')
        else:
            flash('Erro ao conectar ao banco de dados')
            return redirect('/tela_usuario')
    else:
        flash('Usuário não está logado')
        return redirect('/')
    
@app.route('/pag_medico')
def pag_medico():
    # Verifica se o médico está logado
    if 'crm' not in session:
        flash('Por favor, faça login primeiro.')
        return redirect('/login_medico')

    crm_logado = session.get('crm')  # Obtém o CRM da sessão
    # Conecta ao banco de dados MySQL
    conexao_bd = mysql.connector.connect(
        host='localhost', 
        database='consulta_net', 
        user='root', 
        password='gcc272'
    )
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()

            # Seleciona o ID do médico logado
            cursor.execute('SELECT idMedicos FROM medicos WHERE crmMedicos = %s', (crm_logado,))
            id_medico = cursor.fetchone()[0]  # Obtém o ID do médico

            # Seleciona os dados do médico logado
            cursor.execute('''
                SELECT m.nomeMedicos, m.emailMedicos, m.idadeMedicos, m.statusMedicos, m.crmMedicos, 
                       e.nomeEspecialidade, DATE_FORMAT(d.dataDisponibilidade, '%d/%m/%Y') AS dataFormatada, 
                       TIME_FORMAT(d.hora_inicio, '%H:%i'), TIME_FORMAT(d.hora_fim, '%H:%i')
                FROM medicos m
                JOIN medicos_especialidades me ON m.idMedicos = me.idMedico
                JOIN especialidades e ON me.idEspecialidade = e.idEspecialidade
                LEFT JOIN disponibilidade_medicos d ON m.idMedicos = d.idMedico
                WHERE m.crmMedicos = %s
            ''', (crm_logado,))
            
            medico_info = cursor.fetchall()  # Obtém as informações de especialidade e disponibilidade

            cursor.close()
            conexao_bd.close()
            if medico_info:
                # Renderiza a página com as informações do médico e seu ID
                return render_template('pag_medico.html', medico_info=medico_info, id_medico=id_medico)
            else:
                flash('Médico não encontrado.')
                return redirect('/login_medico')
        except mysql.connector.Error as err:
            flash(f'Erro ao conectar ao banco de dados: {err}')
            return redirect('/login_medico')
    else:
        flash('Erro ao conectar ao banco de dados.')
        return redirect('/login_medico')

@app.route('/cadastro_medico', methods=['GET', 'POST'])
def cadastro_medico():
    if request.method == 'POST':
        # Captura os dados do formulário
        nome = request.form.get('nome')
        email = request.form.get('email')
        idade = request.form.get('idade')
        status = request.form.get('status')
        crm = request.form.get('crm')
        senha = request.form.get('senha')
        especialidade = request.form.get('especialidade')
        # Conecta ao banco de dados MySQL
        conexao_bd = mysql.connector.connect(
            host='localhost', 
            database='consulta_net', 
            user='root', 
            password='gcc272'
        )
        cursor = conexao_bd.cursor()
        # Insere os dados do médico na tabela 'medicos'
        cursor.execute('''
            INSERT INTO medicos (nomeMedicos, emailMedicos, idadeMedicos, statusMedicos, crmMedicos, senhaMedicos) 
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (nome, email, idade, status, crm, senha))
        
        idMedico = cursor.lastrowid  # Obtem o ID do médico recém-cadastrado
        # Insere a especialidade na tabela de relacionamento
        cursor.execute('''
            INSERT INTO medicos_especialidades (idMedico, idEspecialidade) 
            VALUES (%s, %s)
        ''', (idMedico, especialidade))
        # Confirma as mudanças no banco de dados
        conexao_bd.commit()
        cursor.close()
        conexao_bd.close()
        return redirect('/pag_medico')
    # Se for um GET, busca as especialidades disponíveis
    conexao_bd = mysql.connector.connect(
        host='localhost', 
        database='consulta_net', 
        user='root', 
        password='gcc272'
    )
    cursor = conexao_bd.cursor()
    cursor.execute('SELECT idEspecialidade, nomeEspecialidade FROM especialidades')
    especialidades = cursor.fetchall()
    cursor.close()
    conexao_bd.close()
    return render_template('cadastro_medico.html', especialidades=especialidades)

@app.route('/login_medico', methods=['GET', 'POST'])
def login_medico():
    if request.method == 'POST':
        crm = request.form.get('crm')
        senha = request.form.get('senha')
        # Verifica se os campos estão preenchidos
        if not crm or not senha:
            flash('CRM e senha são obrigatórios')
            return redirect('/login_medico')
        # Conecta ao banco de dados MySQL
        try:
            conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
            if conexao_bd.is_connected():
                cursor = conexao_bd.cursor()
                cursor.execute('SELECT * FROM medicos WHERE crmMedicos = %s AND senhaMedicos = %s', (crm, senha))
                medico = cursor.fetchone()
                cursor.close()
                conexao_bd.close()

                if medico:
                    # Armazena o CRM na sessão
                    session['crm'] = crm
                    flash('Login realizado com sucesso')
                    return redirect('/pag_medico')  # Redireciona para a página dos médicos
                else:
                    flash('CRM ou senha inválidos')
                    return redirect('/login_medico')
            else:
                flash('Erro ao conectar ao banco de dados')
                return redirect('/login_medico')
        except mysql.connector.Error as err:
            flash(f'Erro ao conectar ao banco de dados: {err}')
            return redirect('/login_medico')
    # Se for uma requisição GET, renderiza a página de login
    return render_template('login_medico.html')

@app.route('/excluir_cadastro_medico', methods=['POST'])
def excluir_cadastro_medico():
    if 'crm' not in session:
        flash('Você precisa estar logado para excluir seu cadastro.')
        return redirect('/login_medico')

    crm = session.get('crm')  # Obtém o CRM da sessão
    # Conecta ao banco de dados MySQL
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()
            # Verifica se o médico realmente existe e obtém o idMedico
            cursor.execute('SELECT idMedicos FROM medicos WHERE crmMedicos = %s', (crm,))
            medico = cursor.fetchone()

            if medico:
                idMedico = medico[0]
                # Excluir registros relacionados na tabela de disponibilidade_medicos
                cursor.execute('DELETE FROM disponibilidade_medicos WHERE idMedico = %s', (idMedico,))
                # Excluir registros relacionados na tabela medicos_especialidades
                cursor.execute('DELETE FROM medicos_especialidades WHERE idMedico = %s', (idMedico,))
                # Em seguida, exclua o médico da tabela 'medicos'
                cursor.execute('DELETE FROM medicos WHERE crmMedicos = %s', (crm,))
                conexao_bd.commit()  # Aplica a exclusão
                # Limpa a sessão após a exclusão
                session.pop('crm', None)

                flash('Cadastro excluído com sucesso.')
                return redirect('/login_medico')
            else:
                flash('Médico não encontrado.')
                return redirect('/pag_medico')

        except mysql.connector.Error as err:
            flash(f'Erro ao excluir o cadastro: {err}')
            return redirect('/pag_medico')

        finally:
            # Certifique-se de que o cursor e a conexão sejam fechados, independentemente do resultado
            if cursor:
                cursor.close()
            if conexao_bd:
                conexao_bd.close()

    else:
        flash('Erro ao conectar ao banco de dados.')
        return redirect('/pag_medico')

@app.route('/atualizar_cadastro_medico', methods=['GET', 'POST'])
def atualizar_cadastro_medico():
    if 'crm' not in session:
        flash('Por favor, faça login primeiro.')
        return redirect('/login_medico')

    crm_logado = session.get('crm')

    if request.method == 'GET':
        conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
        if conexao_bd.is_connected():
            cursor = conexao_bd.cursor()
            cursor.execute('SELECT nomeMedicos, emailMedicos, idadeMedicos, statusMedicos, senhaMedicos, crmMedicos FROM medicos WHERE crmMedicos = %s', (crm_logado,))
            medico = cursor.fetchone()
            cursor.close()
            conexao_bd.close()

            if medico:
                # Renderiza a página de atualização com os dados do médico
                return render_template('atualizar_cadastro_medico.html', medico=medico)
            else:
                flash('Médico não encontrado.')
                return redirect('/pag_medico')
    # Se for uma requisição POST, processa a atualização
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        idade = request.form.get('idade')
        status = request.form.get('status')
        senha = request.form.get('senha')
        # Validação de campos obrigatórios
        if not nome or not email or not idade or not status or not senha:
            flash('Todos os campos são obrigatórios')
            return redirect('/atualizar_cadastro_medico')
        conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
        if conexao_bd.is_connected():
            try:
                cursor = conexao_bd.cursor()
                cursor.execute('''
                    UPDATE medicos
                    SET nomeMedicos = %s, emailMedicos = %s, 
                        idadeMedicos = %s, statusMedicos = %s, senhaMedicos = %s
                    WHERE crmMedicos = %s
                ''', (nome, email, idade, status, senha, crm_logado))
                conexao_bd.commit()
                cursor.close()
                conexao_bd.close()

                flash('Cadastro atualizado com sucesso.')
                return redirect('/pag_medico')
            except mysql.connector.Error as err:
                flash(f'Erro ao atualizar o cadastro: {err}')
                return redirect('/atualizar_cadastro_medico')
        else:
            flash('Erro ao conectar ao banco de dados.')
            return redirect('/atualizar_cadastro_medico')
        
@app.route('/alterar_disponibilidade', methods=['GET', 'POST'])
def alterar_disponibilidade():
    if request.method == 'POST':
        # Conecta ao banco de dados MySQL
        conexao_bd = mysql.connector.connect(
            host='localhost', 
            database='consulta_net', 
            user='root', 
            password='gcc272'
        )
 
        if conexao_bd.is_connected():
            try:
                cursor = conexao_bd.cursor()
                # Capture os dados do formulário
                crm = request.form.get('crm')
                dataDisponibilidade = request.form.get('dataDisponibilidade')
                hora_inicio = request.form.get('hora_inicio')
                hora_fim = request.form.get('hora_fim')
                # Primeiro, busque o ID do médico pelo CRM
                cursor.execute('SELECT idMedicos FROM medicos WHERE crmMedicos = %s', (crm,))
                idMedico = cursor.fetchone()

                if idMedico:
                    # Insira os dados de disponibilidade na tabela de disponibilidade_medicos
                    cursor.execute('''
                        INSERT INTO disponibilidade_medicos (idMedico, dataDisponibilidade, hora_inicio, hora_fim) 
                        VALUES (%s, %s, %s, %s)
                    ''', (idMedico[0], dataDisponibilidade, hora_inicio, hora_fim))
                    conexao_bd.commit()
                    flash('Disponibilidade alterada com sucesso.')
                    return redirect('/pag_medico')  # Redireciona após sucesso
                else:
                    flash('Médico não encontrado.')
                    return redirect('/pag_medico')  # Redireciona em caso de erro

            except mysql.connector.Error as err:
                flash(f'Erro ao alterar disponibilidade: {err}')
                return redirect('/pag_medico')  # Certifique-se de retornar algo em caso de erro

            finally:
                if cursor:
                    cursor.close()
                if conexao_bd:
                    conexao_bd.close()

        else:
            flash('Erro ao conectar ao banco de dados.')
            return redirect('/pag_medico')  # Retorna em caso de falha de conexão
    # Caso o método seja GET, renderize o formulário de disponibilidade
    elif request.method == 'GET':
        crm = request.args.get('crm')
        return render_template('alterar_disponibilidade.html', crm=crm)

@app.route('/agendar_consulta', methods=['POST'])
def agendar_consulta():
    id_disponibilidade = request.form.get('idDisponibilidade')
    hora_inicio = request.form.get('hora_inicio')  # Bloco selecionado
    hora_fim = request.form.get('hora_fim')  # Bloco selecionado
    usuario_logado = session.get('email')  # Obtém o e-mail do usuário logado

    if not usuario_logado:
        flash("Por favor, faça login primeiro.")
        return redirect('/')

    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()

            # Busca o ID do usuário logado
            cursor.execute('SELECT idUsuario FROM usuario WHERE emailUsuario = %s', (usuario_logado,))
            id_usuario = cursor.fetchone()[0]

            # Verifica se o horário já foi reservado (confirmação extra)
            cursor.execute('''
                SELECT COUNT(*) FROM agendamentos
                WHERE idDisponibilidade = %s AND hora_inicio = %s AND hora_fim = %s
            ''', (id_disponibilidade, hora_inicio, hora_fim))
            ja_reservado = cursor.fetchone()[0]

            if ja_reservado > 0:
                flash("Este horário já foi agendado.")
                return redirect('/tela_usuario')

            # Insere o agendamento para o bloco selecionado
            cursor.execute('''
                INSERT INTO agendamentos (idUsuario, idMedico, idDisponibilidade, dataConsulta, hora_inicio, hora_fim)
                SELECT %s, d.idMedico, d.idDisponibilidade, d.dataDisponibilidade, %s, %s
                FROM disponibilidade_medicos d
                WHERE d.idDisponibilidade = %s
            ''', (id_usuario, hora_inicio, hora_fim, id_disponibilidade))

            # Busca informações do agendamento para o e-mail
            cursor.execute('''
                SELECT d.dataDisponibilidade, %s, %s, m.nomeMedicos
                FROM disponibilidade_medicos d
                JOIN medicos m ON d.idMedico = m.idMedicos
                WHERE d.idDisponibilidade = %s
            ''', (hora_inicio, hora_fim, id_disponibilidade))
            consulta_info = cursor.fetchone()

            data_consulta, hora_inicio, hora_fim, nome_medico = consulta_info

            conexao_bd.commit()

            # Enviar o e-mail de confirmação
            data_formatada = data_consulta.strftime('%d/%m/%Y')
            msg = Message("Confirmação de Agendamento", recipients=[usuario_logado])
            msg.body = f'''
            Olá,

            Sua consulta foi agendada com sucesso!
            
            Detalhes da consulta:
            - Dentista: {nome_medico}
            - Data: {data_formatada}
            - Horário: {hora_inicio} - {hora_fim}

            Obrigado por usar nosso serviço!
            '''
            mail.send(msg)

            flash("Consulta agendada com sucesso! E-mail enviado.")
            return redirect('/tela_usuario')
        except mysql.connector.Error as err:
            flash(f"Erro ao agendar consulta: {err}")
            return redirect('/tela_usuario')
        finally:
            cursor.close()
            conexao_bd.close()

@app.route('/consultar_agendamentos', methods=['GET'])
def consultar_agendamentos():
    if 'usuario' not in session:
        flash('Por favor, faça login primeiro.')
        return redirect('/login')
    
    id_usuario = session.get('usuario')
    conexao_bd = mysql.connector.connect(
        host='localhost',
        database='consulta_net',
        user='root',
        password='gcc272'
    )

    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()
            cursor.execute('''
                SELECT a.idAgendamento, m.nomeMedicos, a.dataConsulta, a.hora_inicio, a.hora_fim
                FROM agendamentos a
                JOIN medicos m ON a.idMedico = m.idMedicos
                WHERE a.idUsuario = %s
                ORDER BY a.dataConsulta, a.hora_inicio
            ''', (id_usuario,))
            agendamentos = cursor.fetchall()
            return render_template('consultar_agendamentos.html', agendamentos=agendamentos)
        except mysql.connector.Error as err:
            flash(f'Erro ao consultar agendamentos: {err}')

from datetime import datetime, timedelta # Adicione no início do seu main.py se já não estiver lá, ou dentro da função se preferir.

@app.route('/disponibilidades/<int:id_medico>')
def disponibilidades(id_medico):
    print(f"--- [DEBUG] Entrando em /disponibilidades para id_medico: {id_medico} ---")
    # Certifique-se que datetime e timedelta estão disponíveis no escopo
    # from datetime import datetime, timedelta # Descomente se não estiver global

    conexao_bd = None
    try:
        print("[DEBUG] Tentando conectar ao banco de dados...")
        conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
        print("[DEBUG] Conexão com BD estabelecida.")
        
        # Removido if conexao_bd.is_connected() pois connect() já levanta exceção em falha.
        # O bloco try/except mysql.connector.Error já cobre falhas de conexão.

        cursor = conexao_bd.cursor()
        print("[DEBUG] Cursor criado.")

        print("[DEBUG] Executando query por raw_disponibilidades...")
        cursor.execute('''
            SELECT idDisponibilidade, dataDisponibilidade, hora_inicio, hora_fim
            FROM disponibilidade_medicos
            WHERE idMedico = %s AND dataDisponibilidade >= CURDATE()
        ''', (id_medico,))
        raw_disponibilidades = cursor.fetchall()
        print(f"[DEBUG] raw_disponibilidades: {raw_disponibilidades}")

        print("[DEBUG] Executando query por booked_slots_raw...")
        cursor.execute('''
            SELECT dataConsulta, hora_inicio, hora_fim
            FROM agendamentos
            WHERE idMedico = %s AND dataConsulta >= CURDATE()
        ''', (id_medico,))
        booked_slots_raw = cursor.fetchall()
        print(f"[DEBUG] booked_slots_raw: {booked_slots_raw}")
        
        booked_slots_set = set()
        print("[DEBUG] Processando booked_slots_set...")
        for bs_idx, bs in enumerate(booked_slots_raw):
            # Adicionado tratamento para None em bs[0], bs[1], ou bs[2]
            if bs[0] is None or bs[1] is None or bs[2] is None:
                print(f"[DEBUG]  AVISO: Slot agendado {bs_idx} com dados nulos: {bs}, pulando.")
                continue
            booked_slots_set.add(
                (bs[0], bs[1], bs[2]) 
            )
        print(f"[DEBUG] booked_slots_set: {booked_slots_set}")

        available_blocos = []
        now_datetime = datetime.now()
        print(f"[DEBUG] Data e hora atuais: {now_datetime}")
        print("[DEBUG] Processando available_blocos...")

        for disp_idx, disp in enumerate(raw_disponibilidades):
            print(f"[DEBUG]  Processando disp {disp_idx}: {disp}")
            id_disponibilidade_pai, data_disp_obj, hora_inicio_delta, hora_fim_delta = disp # Renomeado para _delta

            if not all([data_disp_obj, hora_inicio_delta, hora_fim_delta]):
                    print(f"[DEBUG]    AVISO: Dados de disponibilidade incompletos em disp {disp_idx}: {disp}, pulando.")
                    continue
            try:
                    # CONVERSÃO DE TIMEDELTA PARA DATETIME.TIME
                    # Um timedelta é uma duração. Um time é um ponto específico no dia.
                    # Para converter timedelta para time, podemos adicionar o timedelta a uma data de referência (meia-noite)
                    # e então pegar o .time()
                    ref_datetime_midnight = datetime.min # Representa 00:00:00 do ano 1, dia 1
                    
                    hora_inicio_obj = (ref_datetime_midnight + hora_inicio_delta).time()
                    hora_fim_obj = (ref_datetime_midnight + hora_fim_delta).time()
                    
                    # Agora hora_inicio_obj e hora_fim_obj são objetos datetime.time
                    current_slot_start_dt = datetime.combine(data_disp_obj, hora_inicio_obj)
                    final_slot_end_dt = datetime.combine(data_disp_obj, hora_fim_obj)
            except TypeError as te:
                    print(f"[DEBUG]    ERRO DE TIPO ao combinar data/hora para disp {disp_idx}: {te}. Dados originais (delta): {data_disp_obj}, {hora_inicio_delta}, {hora_fim_delta}. Pulando.")
                    continue 
            except AttributeError as ae: # Caso hora_inicio_delta não seja um timedelta
                    print(f"[DEBUG]    ERRO DE ATRIBUTO (possivelmente não é timedelta) para disp {disp_idx}: {ae}. Dados originais: {data_disp_obj}, {hora_inicio_delta}, {hora_fim_delta}. Pulando.")
                    continue
            print(f"[DEBUG]    Slot pai (disponibilidade original): de {current_slot_start_dt} a {final_slot_end_dt}")
            
            while current_slot_start_dt < final_slot_end_dt:
                slot_end_candidate_dt = current_slot_start_dt + timedelta(minutes=30)
                actual_slot_end_dt = min(slot_end_candidate_dt, final_slot_end_dt)
                print(f"[DEBUG]      Bloco candidato: {current_slot_start_dt.time()} - {actual_slot_end_dt.time()} em {data_disp_obj.strftime('%d/%m/%Y')}")

                is_booked = (
                    data_disp_obj, 
                    current_slot_start_dt.time(), 
                    actual_slot_end_dt.time()
                ) in booked_slots_set
                print(f"[DEBUG]        Está agendado? {is_booked}")
                
                if current_slot_start_dt >= now_datetime and not is_booked:
                    print("[DEBUG]        ADICIONANDO bloco à lista de disponíveis.")
                    available_blocos.append({
                        "idDisponibilidade": id_disponibilidade_pai,
                        "dataDisponibilidade": data_disp_obj.strftime('%d/%m/%Y'),
                        "hora_inicio": current_slot_start_dt.strftime('%H:%M'),
                        "hora_fim": actual_slot_end_dt.strftime('%H:%M'),
                        "idMedico": id_medico,
                    })
                else:
                    if not (current_slot_start_dt >= now_datetime):
                        print("[DEBUG]        NÃO ADICIONANDO: Bloco candidato já passou.")
                    if is_booked:
                        print("[DEBUG]        NÃO ADICIONANDO: Bloco candidato já está agendado.")

                current_slot_start_dt = actual_slot_end_dt
        
        print(f"[DEBUG] available_blocos final: {available_blocos}")
        # Fechar cursor aqui se tudo deu certo antes de renderizar
        if cursor:
            cursor.close()
        print("[DEBUG] Renderizando disponibilidades.html...")
        return render_template('disponibilidades.html', disponibilidades=available_blocos, id_medico=id_medico)

    except mysql.connector.Error as err:
        print(f"[DEBUG] !!! Erro MySQL: {err} !!!")
        flash(f"Erro de banco de dados ao buscar disponibilidades: {err}", "error")
        return redirect(url_for('tela_medico'))
    except Exception as e:
        import traceback # Para obter o stack trace completo do erro
        print(f"[DEBUG] !!! Erro Geral Inesperado: {e} !!!")
        print(traceback.format_exc()) # Imprime o stack trace completo no console
        flash(f"Erro inesperado ao processar disponibilidades: {str(e)}", "error")
        return redirect(url_for('tela_medico'))
    finally:
        if conexao_bd and conexao_bd.is_connected():
            print("[DEBUG] Fechando conexão com BD no finally.")
            if 'cursor' in locals() and cursor: # Garante que o cursor seja fechado se foi aberto
                cursor.close()
            conexao_bd.close()
        
@app.route('/calendario_medico/<int:id_medico>')
def calendario_medico(id_medico):
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()
            cursor.execute('''
                SELECT DATE_FORMAT(d.dataDisponibilidade, '%d/%m/%Y') AS dataFormatada, d.hora_inicio, d.hora_fim, u.nomeUsuario, a.idAgendamento
                FROM disponibilidade_medicos d
                LEFT JOIN agendamentos a ON d.idDisponibilidade = a.idDisponibilidade
                LEFT JOIN usuario u ON a.idUsuario = u.idUsuario
                WHERE d.idMedico = %s
            ''', (id_medico,))
            consultas = cursor.fetchall()

            cursor.close()
            conexao_bd.close()
            return render_template('calendario_medico.html', consultas=consultas, id_medico=id_medico)
        except mysql.connector.Error as err:
            flash(f"Erro ao carregar o calendário: {err}")
            return redirect('/pag_medico')

@app.route('/cancelar_consulta', methods=['POST'])
def cancelar_consulta():
    id_agendamento = request.form.get('idAgendamento')
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()

            # Busca informações do agendamento antes de excluí-lo
            cursor.execute('''
                SELECT u.emailUsuario, d.dataDisponibilidade, a.hora_inicio, a.hora_fim, m.nomeMedicos, m.idMedicos
                FROM agendamentos a
                JOIN usuario u ON a.idUsuario = u.idUsuario
                JOIN disponibilidade_medicos d ON a.idDisponibilidade = d.idDisponibilidade
                JOIN medicos m ON a.idMedico = m.idMedicos
                WHERE a.idAgendamento = %s
            ''', (id_agendamento,))
            agendamento = cursor.fetchone()

            if not agendamento:
                flash("Agendamento não encontrado.")
                return redirect('/calendario_medico')

            email_usuario, data_consulta, hora_inicio, hora_fim, nome_medico, id_medico = agendamento

            # Remove o agendamento do banco de dados
            cursor.execute('DELETE FROM agendamentos WHERE idAgendamento = %s', (id_agendamento,))
            conexao_bd.commit()

            # Formata a data para o e-mail
            data_formatada = data_consulta.strftime('%d/%m/%Y')

            # Envia o e-mail de aviso ao usuário
            msg = Message("Aviso de Cancelamento de Consulta", recipients=[email_usuario])
            msg.body = f'''
            Olá,

            Infelizmente, sua consulta foi cancelada pelo Dentista.

            Detalhes da consulta cancelada:
            - Dentista: {nome_medico}
            - Data: {data_formatada}
            - Horário: {hora_inicio} - {hora_fim}

            Por favor, acesse nosso sistema para reagendar sua consulta.

            Pedimos desculpas pelo transtorno.
            '''
            mail.send(msg)

            flash("Consulta cancelada com sucesso! Usuário notificado por e-mail.")
            return redirect(f'/calendario_medico/{id_medico}')  # Redireciona para o calendário do médico
        except mysql.connector.Error as err:
            flash(f"Erro ao cancelar consulta: {err}")
            return redirect(f'/calendario_medico/{id_medico}')  # Redireciona em caso de erro
        finally:
            cursor.close()
            conexao_bd.close()

@app.route('/gerenciar_disponibilidades/<int:id_medico>')
def gerenciar_disponibilidades(id_medico):
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()
            # Busca todas as disponibilidades do médico
            cursor.execute('''
                SELECT d.idDisponibilidade, DATE_FORMAT(d.dataDisponibilidade, '%d/%m/%Y') AS dataFormatada, 
                       TIME_FORMAT(d.hora_inicio, '%H:%i') AS horaInicio, TIME_FORMAT(d.hora_fim, '%H:%i') AS horaFim
                FROM disponibilidade_medicos d
                WHERE d.idMedico = %s AND d.dataDisponibilidade >= CURDATE()
            ''', (id_medico,))
            disponibilidades = cursor.fetchall()

            cursor.close()
            conexao_bd.close()
            return render_template('gerenciar_disponibilidades.html', disponibilidades=disponibilidades, id_medico=id_medico)
        except mysql.connector.Error as err:
            flash(f"Erro ao carregar as disponibilidades: {err}")
            return redirect('/pag_medico')

@app.route('/excluir_disponibilidade', methods=['POST'])
def excluir_disponibilidade():
    id_disponibilidade = request.form.get('idDisponibilidade')
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()
            cursor.execute('DELETE FROM disponibilidade_medicos WHERE idDisponibilidade = %s', (id_disponibilidade,))
            conexao_bd.commit()

            flash("Disponibilidade excluída com sucesso!")
            return redirect(request.referrer)
        except mysql.connector.Error as err:
            flash(f"Erro ao excluir disponibilidade: {err}")
            return redirect(request.referrer)
        finally:
            cursor.close()
            conexao_bd.close()

#inicia Flask
if __name__ == "__main__":
    app.run(debug=True)

    