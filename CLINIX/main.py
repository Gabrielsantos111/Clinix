from flask import Flask, render_template, redirect, request, flash, send_from_directory, session, url_for
import json
import ast
import os
import urllib.parse  # <--- ADICIONADO PARA LER A URL DO BANCO
import mysql.connector
import random
import string
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

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

# --- CONFIGURAÇÃO CENTRAL DE BANCO DE DADOS ---
DATABASE_URL = os.environ.get('DATABASE_URL')
BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')

def get_db_connection():
    """
    Cria e retorna uma nova conexão com o banco de dados.
    Lê a URL de conexão a partir das variáveis de ambiente.
    """
    if not DATABASE_URL:
        # Se não encontrar a variável no Vercel, vai dar este erro claro.
        raise ValueError("A variável de ambiente 'DATABASE_URL' não foi definida.")
    
    # O urllib.parse vai quebrar a URL (mysql://user:pass@host:port/db)
    try:
        parsed_url = urllib.parse.urlparse(DATABASE_URL)
        
        db_host = parsed_url.hostname
        db_port = parsed_url.port
        db_user = parsed_url.username
        db_password = parsed_url.password
        db_name = parsed_url.path[1:] # Remove a barra "/" inicial

        # Conecta usando as credenciais da variável de ambiente
        conexao = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        return conexao
    except mysql.connector.Error as err:
        # Isso ajudará a depurar erros de conexão nos logs do Vercel
        print(f"ERRO AO CONECTAR AO BANCO DE DADOS: {err}")
        raise err # Levanta o erro para parar a execução da rota
    except Exception as e:
        # Pega outros erros (ex: URL mal formatada)
        print(f"ERRO AO PARSEAR DATABASE_URL: {e}")
        raise ValueError(f"DATABASE_URL mal formatada: {DATABASE_URL}")

# --- FIM DA CONFIGURAÇÃO DE BANCO DE DADOS ---


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
    conexao_bd = get_db_connection() # <-- ALTERADO
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
    conexao_bd = get_db_connection() # <-- ALTERADO
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
    # REMOVIDA: A linha 'logado = False' foi removida.
    return render_template('login.html')

#rota página download
@app.route('/pag_download')
def pag_download():
    # CORREÇÃO: Trocado 'if logado:' por 'if 'email' in session:'
    if 'email' in session: 
        arquivo = []
        for documento in os.listdir('arquivos'):
            arquivo.append(documento)  #add os nomes dos arquivos na lista
        return render_template("pag_download.html", arquivos=arquivo)  
    else:
        return redirect('/')  
    
# --- ROTA MODIFICADA ---
@app.route('/tela_usuario')
def tela_usuario():
    # Verifica se o usuário está logado
    if 'email' in session:
        email_do_usuario_logado = session.get('email')
        if email_do_usuario_logado:
            # 1. Busca informações do usuário (para os botões de perfil)
            usuario = obter_informacoes_usuario(email_do_usuario_logado)
            if usuario:
                # 2. Busca a lista de médicos ativos
                medicos = [] # Lista padrão
                conexao_bd = get_db_connection() # <-- ALTERADO
                if conexao_bd.is_connected():
                    try:
                        cursor = conexao_bd.cursor()
                        # Query para buscar médicos ATIVOS
                        cursor.execute('''
                            SELECT m.idMedicos, m.nomeMedicos, m.emailMedicos, m.idadeMedicos, m.statusMedicos, GROUP_CONCAT(e.nomeEspecialidade SEPARATOR ', ')
                            FROM medicos m
                            JOIN medicos_especialidades me ON m.idMedicos = me.idMedico
                            JOIN especialidades e ON me.idEspecialidade = e.idEspecialidade
                            WHERE m.statusMedicos = 'Ativo'
                            GROUP BY m.idMedicos, m.nomeMedicos, m.emailMedicos, m.idadeMedicos, m.statusMedicos
                        ''')
                        medicos = cursor.fetchall()
                        cursor.close()
                        conexao_bd.close()
                    except mysql.connector.Error as err:
                        flash(f"Erro ao carregar médicos: {err}")
                        # Continua mesmo se houver erro, apenas com a lista vazia
                
                # 3. Envia ambos (usuário e médicos) para o template
                return render_template('tela_usuario.html', usuario=usuario, medicos=medicos)
        
        flash('Erro ao obter informações do usuário')
        return redirect('/')
    else:
        # Se não estiver logado, redireciona para o login
        return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # REMOVIDA: 'global logado' não é mais necessária aqui.

    if request.method == 'GET':
        # Renderiza a página de login no método GET
        return render_template('login.html')

    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        # Conecta ao banco de dados MySQL
        conexao_bd = get_db_connection() # <-- ALTERADO
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
                        # REMOVIDA: 'logado = True'
                        session['email'] = email
                        return redirect("/adm")

                    # Verifica se o e-mail e a senha do usuário são válidos
                    if usuarioNome == email and usuarioSenha == senha:
                        # REMOVIDA: 'logado = True'
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
    # REMOVIDA: 'global logado'
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
    conexao_bd = get_db_connection() # <-- ALTERADO
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
    # REMOVIDA: 'global logado' e 'logado = True'

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
    conexao_bd = get_db_connection() # <-- ALTERADO
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
            link = f"{BASE_URL}/redefinir_senha/{token}"
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
        conexao_bd = get_db_connection() # <-- ALTERADO
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

    # Correção de redefinição de senha (já aplicada antes)
    return render_template('redefinir_senha.html', token=token)

@app.route('/tela_medico')
def tela_medico():
    # CORREÇÃO: Trocado 'if logado:' por 'if 'email' in session:'
    # Esta rota deve ser acessível se o usuário estiver logado
    if 'email' in session: 
        conexao_bd = get_db_connection() # <-- ALTERADO
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
    # CORREÇÃO: Trocado 'if logado:' por 'if 'email' in session:'
    if 'email' in session:
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
    # CORREÇÃO: Trocado 'if logado:' por 'if 'email' in session:'
    if 'email' in session:
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
        conexao_bd = get_db_connection() # <-- ALTERADO
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
    # CORREÇÃO: Trocado 'if logado:' por 'if 'email' in session:'
    if 'email' in session:
        return render_template('confirmar_exclusao.html')
    else:
        return redirect('/')

@app.route('/excluir_cadastro', methods=['POST'])
def excluir_cadastro():
    # CORREÇÃO: Trocado 'if logado:' por 'if 'email' in session:'
    if 'email' in session:
        email = session.get('email')
        # Conecta ao banco de dados MySQL
        conexao_bd = get_db_connection() # <-- ALTERADO
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
    conexao_bd = get_db_connection() # <-- ALTERADO
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()

            # Query 1: Buscar os dados principais do médico
            cursor.execute('''
                SELECT m.idMedicos, m.nomeMedicos, m.emailMedicos, m.idadeMedicos, m.statusMedicos, m.crmMedicos, e.nomeEspecialidade
                FROM medicos m
                JOIN medicos_especialidades me ON m.idMedicos = me.idMedico
                JOIN especialidades e ON me.idEspecialidade = e.idEspecialidade
                WHERE m.crmMedicos = %s
            ''', (crm_logado,))
            medico_info = cursor.fetchone() # Usamos fetchone() pois esperamos apenas um médico

            if not medico_info:
                flash('Médico não encontrado.')
                return redirect('/login_medico')

            id_medico = medico_info[0]

            # Query 2: Buscar as disponibilidades do médico
            cursor.execute('''
                SELECT DATE_FORMAT(dataDisponibilidade, '%d/%m/%Y'), 
                       TIME_FORMAT(hora_inicio, '%H:%i'), 
                       TIME_FORMAT(hora_fim, '%H:%i')
                FROM disponibilidade_medicos
                WHERE idMedico = %s
            ''', (id_medico,))
            disponibilidades = cursor.fetchall()

            cursor.close()
            conexao_bd.close()
            
            # Renderiza a página com as informações do médico e sua disponibilidade
            return render_template('pag_medico.html', medico_info=medico_info, disponibilidades=disponibilidades, id_medico=id_medico)

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
        conexao_bd = get_db_connection() # <-- ALTERADO
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
    conexao_bd = get_db_connection() # <-- ALTERADO
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
            conexao_bd = get_db_connection() # <-- ALTERADO
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
    conexao_bd = get_db_connection() # <-- ALTERADO
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
        conexao_bd = get_db_connection() # <-- ALTERADO
        if conexao_bd.is_connected():
            cursor = conexao_bd.cursor()
            # Correção de índice já aplicada
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
        conexao_bd = get_db_connection() # <-- ALTERADO
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

# --- ROTA MODIFICADA (Lógica de quebra de blocos) ---
@app.route('/alterar_disponibilidade', methods=['GET', 'POST'])
def alterar_disponibilidade():
    # Apenas médicos logados podem alterar
    if 'crm' not in session:
        flash('Por favor, faça login de médico primeiro.')
        return redirect('/login_medico')

    if request.method == 'POST':
        conexao_bd = get_db_connection() # <-- ALTERADO
 
        if conexao_bd.is_connected():
            try:
                cursor = conexao_bd.cursor()
                
                crm = request.form.get('crm')
                dataDisponibilidade = request.form.get('dataDisponibilidade')
                bloco_manha = request.form.get('bloco_manha') # Valor '08:00-12:00'
                bloco_tarde = request.form.get('bloco_tarde') # Valor '14:00-18:00'
                hora_inicio_custom = request.form.get('hora_inicio')
                hora_fim_custom = request.form.get('hora_fim')

                cursor.execute('SELECT idMedicos FROM medicos WHERE crmMedicos = %s', (crm,))
                idMedico = cursor.fetchone()

                if not idMedico:
                    flash('Médico não encontrado.')
                    return redirect('/pag_medico')

                # Lista de blocos-pai para processar (ex: '08:00', '12:00')
                blocos_para_processar = []
                
                if bloco_manha:
                    blocos_para_processar.append(bloco_manha.split('-')) # Adiciona ['08:00', '12:00']
                    
                if bloco_tarde:
                    blocos_para_processar.append(bloco_tarde.split('-')) # Adiciona ['14:00', '18:00']

                if hora_inicio_custom and hora_fim_custom:
                    blocos_para_processar.append([hora_inicio_custom, hora_fim_custom])

                if not blocos_para_processar:
                    flash('Nenhum horário selecionado. Por favor, marque um bloco ou insira um horário personalizado.')
                    return redirect(f'/alterar_disponibilidade?crm={crm}')

                # --- Início da Lógica de Quebra de Bloco ---
                
                # Lista final de slots de 30 minutos (ex: '08:00', '08:30')
                slots_para_inserir = []
                formato_hora = '%H:%M'
                data_ref = datetime(2000, 1, 1) # Data de referência para cálculos
                delta_30_min = timedelta(minutes=30)

                for inicio_str, fim_str in blocos_para_processar:
                    try:
                        inicio_dt = datetime.combine(data_ref, datetime.strptime(inicio_str, formato_hora).time())
                        fim_dt = datetime.combine(data_ref, datetime.strptime(fim_str, formato_hora).time())
                        
                        current_dt = inicio_dt
                        while current_dt < fim_dt:
                            next_dt = current_dt + delta_30_min
                            # Garante que não ultrapasse o tempo final
                            if next_dt > fim_dt:
                                next_dt = fim_dt
                            
                            slots_para_inserir.append((
                                current_dt.strftime(formato_hora), 
                                next_dt.strftime(formato_hora)
                            ))
                            current_dt = next_dt

                    except ValueError:
                        flash(f'Formato de hora inválido: {inicio_str}-{fim_str}')
                        continue
                
                # --- Fim da Lógica de Quebra de Bloco ---

                # Loop para inserir todos os slots de 30 minutos
                for inicio, fim in slots_para_inserir:
                    cursor.execute('''
                        INSERT INTO disponibilidade_medicos (idMedico, dataDisponibilidade, hora_inicio, hora_fim) 
                        VALUES (%s, %s, %s, %s)
                    ''', (idMedico[0], dataDisponibilidade, inicio, fim))
                
                conexao_bd.commit()
                flash(f'{len(slots_para_inserir)} horários adicionados com sucesso para {dataDisponibilidade}.')
                return redirect('/pag_medico')  # Redireciona após sucesso

            except mysql.connector.Error as err:
                flash(f'Erro ao alterar disponibilidade: {err}')
                return redirect('/pag_medico')

            finally:
                if cursor:
                    cursor.close()
                if conexao_bd:
                    conexao_bd.close()

        else:
            flash('Erro ao conectar ao banco de dados.')
            return redirect('/pag_medico')
    
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

    conexao_bd = get_db_connection() # <-- ALTERADO
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
    if 'email' not in session: # CORREÇÃO: Usar 'email'
        flash('Por favor, faça login primeiro.')
        return redirect('/login')
    
    email_usuario = session.get('email') # CORREÇÃO: Obter o email
    conexao_bd = get_db_connection() # <-- ALTERADO

    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()
            
            # CORREÇÃO: Buscar idUsuario a partir do email
            cursor.execute('SELECT idUsuario FROM usuario WHERE emailUsuario = %s', (email_usuario,))
            resultado = cursor.fetchone()
            if not resultado:
                flash('Usuário não encontrado.')
                return redirect('/')
            id_usuario = resultado[0]

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
            return redirect('/tela_usuario')
        finally:
            if conexao_bd.is_connected():
                cursor.close()
                conexao_bd.close()

from datetime import datetime, timedelta # Adicione no início do seu main.py se já não estiver lá, ou dentro da função se preferir.

@app.route('/disponibilidades/<int:id_medico>')
def disponibilidades(id_medico):
    print(f"--- [DEBUG] Entrando em /disponibilidades para id_medico: {id_medico} ---")
    # Certifique-se que datetime e timedelta estão disponíveis no escopo
    # from datetime import datetime, timedelta # Descomente se não estiver global

    conexao_bd = None
    try:
        print("[DEBUG] Tentando conectar ao banco de dados...")
        conexao_bd = get_db_connection() # <-- ALTERADO
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
        ref_datetime_midnight = datetime.min # Adicione esta linha de referência
        
        for bs_idx, bs in enumerate(booked_slots_raw):
            # Adicionado tratamento para None em bs[0], bs[1], ou bs[2]
            if bs[0] is None or bs[1] is None or bs[2] is None:
                print(f"[DEBUG]  AVISO: Slot agendado {bs_idx} com dados nulos: {bs}, pulando.")
                continue
            
            # --- INÍCIO DA CORREÇÃO ---
            # Converte os timedeltas de hora_inicio e hora_fim para objetos time
            hora_inicio_agendada = (ref_datetime_midnight + bs[1]).time()
            hora_fim_agendada = (ref_datetime_midnight + bs[2]).time()
            
            booked_slots_set.add(
                (bs[0], hora_inicio_agendada, hora_fim_agendada) # Adiciona os valores convertidos
            )
            # --- FIM DA CORREÇÃO ---
            
        print(f"[DEBUG] booked_slots_set: {booked_slots_set}")

        available_blocos = []
        now_datetime = datetime.now()
        print(f"[DEBUG] Data e hora atuais: {now_datetime}")
        print("[DEBUG] Processando available_blocos...")

        # --- AVISO: LÓGICA DE QUEBRA DE BLOCOS REMOVIDA DESTA ROTA ---
        # A lógica de quebra de blocos foi movida para a inserção (alterar_disponibilidade)
        # Esta rota agora apenas exibe os slots de 30 minutos que já estão no banco.
        
        for disp_idx, disp in enumerate(raw_disponibilidades):
            print(f"[DEBUG]  Processando disp {disp_idx}: {disp}")
            id_disponibilidade_pai, data_disp_obj, hora_inicio_delta, hora_fim_delta = disp # Renomeado para _delta

            if not all([data_disp_obj, hora_inicio_delta, hora_fim_delta]):
                    print(f"[DEBUG]    AVISO: Dados de disponibilidade incompletos em disp {disp_idx}: {disp}, pulando.")
                    continue
            try:
                    ref_datetime_midnight = datetime.min
                    hora_inicio_obj = (ref_datetime_midnight + hora_inicio_delta).time()
                    hora_fim_obj = (ref_datetime_midnight + hora_fim_delta).time()
                    
                    slot_start_dt = datetime.combine(data_disp_obj, hora_inicio_obj)
                    slot_end_dt = datetime.combine(data_disp_obj, hora_fim_obj)
            
            except Exception as e: 
                    print(f"[DEBUG]    ERRO ao processar disp {disp_idx}: {e}. Dados: {disp}. Pulando.")
                    continue
            
            print(f"[DEBUG]      Slot de 30min: {slot_start_dt.time()} - {slot_end_dt.time()} em {data_disp_obj.strftime('%d/%m/%Y')}")

            is_booked = (
                data_disp_obj, 
                slot_start_dt.time(), 
                slot_end_dt.time()
            ) in booked_slots_set
            print(f"[DEBUG]        Está agendado? {is_booked}")
            
            if slot_start_dt >= now_datetime and not is_booked:
                print("[DEBUG]        ADICIONANDO bloco à lista de disponíveis.")
                available_blocos.append({
                    "idDisponibilidade": id_disponibilidade_pai,
                    "dataDisponibilidade": data_disp_obj.strftime('%d/%m/%Y'),
                    "hora_inicio": slot_start_dt.strftime('%H:%M'),
                    "hora_fim": slot_end_dt.strftime('%H:%M'),
                    "idMedico": id_medico,
                })
            else:
                if not (slot_start_dt >= now_datetime):
                    print("[DEBUG]        NÃO ADICIONANDO: Slot já passou.")
                if is_booked:
                    print("[DEBUG]        NÃO ADICIONANDO: Slot já está agendado.")

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

# --- ROTA MODIFICADA (QUERY CORRIGIDA) ---
@app.route('/calendario_medico/<int:id_medico>')
def calendario_medico(id_medico):
    conexao_bd = get_db_connection() # <-- ALTERADO
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()
            
            # --- INÍCIO DA CORREÇÃO ---
            # Esta query agora funciona perfeitamente com os slots de 30min
            cursor.execute('''
                SELECT 
                    DATE_FORMAT(d.dataDisponibilidade, '%d/%m/%Y') AS dataFormatada, 
                    IFNULL(TIME_FORMAT(a.hora_inicio, '%H:%i'), TIME_FORMAT(d.hora_inicio, '%H:%i')) AS hora_inicio_final,
                    IFNULL(TIME_FORMAT(a.hora_fim, '%H:%i'), TIME_FORMAT(d.hora_fim, '%H:%i')) AS hora_fim_final,
                    u.nomeUsuario, 
                    a.idAgendamento
                FROM 
                    disponibilidade_medicos d
                LEFT JOIN 
                    agendamentos a ON d.idDisponibilidade = a.idDisponibilidade
                LEFT JOIN 
                    usuario u ON a.idUsuario = u.idUsuario
                WHERE 
                    d.idMedico = %s
                ORDER BY 
                    dataFormatada, hora_inicio_final;
            ''', (id_medico,))
            # --- FIM DA CORREÇÃO ---
            
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
    conexao_bd = get_db_connection() # <-- ALTERADO
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
    conexao_bd = get_db_connection() # <-- ALTERADO
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
    conexao_bd = get_db_connection() # <-- ALTERADO
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