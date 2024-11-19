from flask import Flask, render_template, redirect, request, flash, send_from_directory, session, url_for
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

@app.route('/tela_medico')
def tela_medico():
    if logado:
        conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
        if conexao_bd.is_connected():
            try:
                cursor = conexao_bd.cursor()
                cursor.execute('''
                    SELECT m.nomeMedicos, m.emailMedicos, m.idadeMedicos, m.statusMedicos, GROUP_CONCAT(e.nomeEspecialidade SEPARATOR ', ')
                    FROM medicos m
                    JOIN medicos_especialidades me ON m.idMedicos = me.idMedico
                    JOIN especialidades e ON me.idEspecialidade = e.idEspecialidade
                    GROUP BY m.idMedicos
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
            # Seleciona os dados do médico logado
            cursor.execute('''
                SELECT m.nomeMedicos, m.emailMedicos, m.idadeMedicos, m.statusMedicos, m.crmMedicos, e.nomeEspecialidade, DATE_FORMAT(d.dataDisponibilidade, '%d/%m/%Y') AS dataFormatada, d.hora_inicio, d.hora_fim
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
                # Renderiza a página com as informações do médico
                return render_template('pag_medico.html', medico_info=medico_info)
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
    hora_inicio = request.form.get('hora_inicio')
    hora_fim = request.form.get('hora_fim')
    usuario_logado = session.get('email')

    if not usuario_logado:
        flash("Por favor, faça login primeiro.")
        return redirect('/')

    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()
            cursor.execute('SELECT idUsuario FROM usuario WHERE emailUsuario = %s', (usuario_logado,))
            id_usuario = cursor.fetchone()[0]

            cursor.execute('''
                SELECT idMedico, dataDisponibilidade
                FROM disponibilidade_medicos
                WHERE idDisponibilidade = %s
            ''', (id_disponibilidade,))
            disponibilidade = cursor.fetchone()

            if disponibilidade:
                id_medico, data_consulta = disponibilidade
                cursor.execute('''
                    INSERT INTO agendamentos (idUsuario, idMedico, idDisponibilidade, dataConsulta, hora_inicio, hora_fim)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (id_usuario, id_medico, id_disponibilidade, data_consulta, hora_inicio, hora_fim))

                conexao_bd.commit()
                flash("Consulta agendada com sucesso!")
                return redirect('/tela_usuario')
            else:
                flash("Disponibilidade não encontrada.")
                return redirect('/tela_medico')
        except mysql.connector.Error as err:
            flash(f"Erro ao agendar consulta: {err}")
            return redirect('/tela_medico')
        finally:
            cursor.close()
            conexao_bd.close()
    else:
        flash("Erro ao conectar ao banco de dados.")
        return redirect('/')

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

from datetime import timedelta

@app.route('/disponibilidades/<int:id_medico>')
def disponibilidades(id_medico):
    conexao_bd = mysql.connector.connect(host='localhost', database='consulta_net', user='root', password='gcc272')
    from datetime import datetime
    if conexao_bd.is_connected():
        try:
            cursor = conexao_bd.cursor()
            cursor.execute('''
                SELECT idDisponibilidade, DATE_FORMAT(dataDisponibilidade, '%d/%m/%Y') AS dataFormatada, TIME_FORMAT(hora_inicio, '%H:%i'), TIME_FORMAT(hora_fim, '%H:%i')
                FROM disponibilidade_medicos
                WHERE idMedico = %s AND dataDisponibilidade >= CURDATE()
            ''', (id_medico,))
            disponibilidades = cursor.fetchall()

            # Dividir horários em blocos de 30 minutos
            blocos = []
            for disp in disponibilidades:
                id_disponibilidade, data_disponibilidade, hora_inicio, hora_fim = disp
                hora_inicio = datetime.strptime(hora_inicio, '%H:%M')
                hora_fim = datetime.strptime(hora_fim, '%H:%M')
                while hora_inicio < hora_fim:
                    bloco_inicio = hora_inicio
                    bloco_fim = bloco_inicio + timedelta(minutes=30)
                    if bloco_fim > hora_fim:
                        bloco_fim = hora_fim
                    blocos.append((
                        id_disponibilidade,
                        data_disponibilidade,
                        bloco_inicio.strftime('%H:%M'),  # Garante que bloco_inicio seja string
                        bloco_fim.strftime('%H:%M')  # Garante que bloco_fim seja string
                    ))
                    hora_inicio = bloco_fim

            cursor.close()
            conexao_bd.close()
            return render_template('disponibilidades.html', disponibilidades=blocos, id_medico=id_medico)
        except mysql.connector.Error as err:
            flash(f"Erro ao buscar disponibilidades: {err}")
            return redirect('/tela_medico')

#inicia Flask
if __name__ == "__main__":
    app.run(debug=True)