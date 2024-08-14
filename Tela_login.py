from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

# Simulação de banco de dados
usuarios = {'usuario@example.com': 'senha123'}

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    senha = request.form['senha']
    if email in usuarios and usuarios[email] == senha:
        flash('Login realizado com sucesso!', 'success')
        return redirect(url_for('home'))
    else:
        flash('Email ou senha incorretos.', 'danger')
        return redirect(url_for('home'))

@app.route('/esqueci_senha')
def esqueci_senha():
    return render_template('esqueci_senha.html')

@app.route('/esqueci_senha', methods=['POST'])
def esqueci_senha_post():
    email = request.form['email']
    if email in usuarios:
        flash('Instruções de recuperação de senha enviadas para seu email.', 'info')
    else:
        flash('Email não encontrado.', 'danger')
    return redirect(url_for('esqueci_senha'))

if __name__ == '__main__':
    app.run(debug=True)
