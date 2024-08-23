from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

usuarios = {'ufgjklfmyjçfltkypedt
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    senha = request.form['senha']
    if email in usuarios and usuarios[email] == senha:
        user = User(email)
        login_user(user)
        flash('Login realizado com sucesso!', 'success')
        return redirect(url_for('pagina_principal'))
    else:
        flash('Email ou senha incorretos.', 'danger')
        return redirect(url_for('home'))
    
@app.route('/pagina_principal')
@login_required
def pagina_principal():
    return render_template('pagina_principal.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
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
