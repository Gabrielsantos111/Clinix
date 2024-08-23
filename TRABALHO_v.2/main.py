from flask import Flask, render_template, redirect, request, flash
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gabdan2004'

logado = False


@app.route('/')
def home():
    global logado
    logado = False
    return render_template('login.html')

@app.route('/adm')
def adm():
    if logado == True:
        return render_template("administrador.html")
    if logado == False:
        return redirect('/')

@app.route('/login', methods=['POST'])
def login():

    global logado

    email = request.form.get('email')
    senha = request.form.get('senha')


    with open('usuarios.json') as usuariosTemp:
        usuarios = json.load(usuariosTemp)
        cont = 0
        for usuario in usuarios:
            cont += 1
            if email == 'adm' and senha == '000':
                logado = True
                return redirect("/adm")
            
            if usuario['email'] == email and usuario['senha'] == senha:
                return render_template("usuario.html")
            
            if cont >= len(usuarios):
                flash('USUARIO INVALIDO')
                return redirect("/")

@app.route('/cadastrarUsuario', methods=['POST'])
def cadastrarUsuario():
    user = []
    email = request.form.get('email')
    senha = request.form.get('senha')
    user = [
        {
            "email": email,
            "senha": senha
        }
    ]
    with open('usuarios.json') as usuariosTemp:
        usuarios = json.load(usuariosTemp)

    usuarioNovo = usuarios + user

    with open('usuarios.json', 'w') as gravarTemp:
        json.dump(usuarioNovo, gravarTemp, indent=4 )

    return redirect('/adm')



if __name__ in "__main__":
    app.run(debug=True)