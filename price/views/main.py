from flask import Blueprint, render_template, current_app, flash, redirect, url_for, request, abort
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo

# Classe estrutural para o Login
class LoginForm(FlaskForm):
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

# Nova classe estrutural para o Cadastro (SignUp)
class SignUpForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    confirmar_senha = PasswordField('Confirmar Senha', validators=[
        DataRequired(), 
        EqualTo('senha', message='As senhas devem ser iguais.')
    ])
    submit = SubmitField('Criar Conta')

bp_main = Blueprint("main", __name__)


@bp_main.route("/")
def index():
    return render_template("main/index.html", usuario_logado=False)


@bp_main.route("/dashboard")
def dashboard():
    return render_template("main/dashboard.html", usuario_logado=False)


@bp_main.route("/search")
def search():
    return render_template("main/search.html", usuario_logado=False)


@bp_main.route("/monitored")
def monitored():
    return render_template("main/monitored.html", usuario_logado=False)


@bp_main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        return redirect(url_for("main.index"))
    return render_template("main/login.html", form=form, usuario_logado=False)


@bp_main.route("/signup", methods=["GET", "POST"])
def signup():
    # Instanciando o formulário de cadastro para o WTForms funcionar no Jinja
    form = SignUpForm()
    
    if form.validate_on_submit():
        flash("Conta criada com sucesso! Faça seu login.", "success")
        return redirect(url_for("main.login"))
        
    return render_template("main/signup.html", form=form, usuario_logado=False)


@bp_main.route("/logout")
def logout():
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("main.index"))


# @bp_main.route('/')
# @bp_main.route('/index')
# def index():
#     current_app.logger.debug("Renderizando template index.html dinamico")
# ... (restante do código legado comentado preservado)


# @bp_main.route('/')
# @bp_main.route('/index')
# def index():
#     current_app.logger.debug("Renderizando template index.html dinamico")

#     # 1. Recupera o usuario Pedro Jose via API de consulta do ORM
#     # Utilizamos o e-mail como chave de busca por integridade de dominio
#     user = User.query.filter_by(email="pedro@email.com").first()

#     # Gatilho de seguranca: se o banco nao foi semeado, interrompe a requisicao
#     if not user:
#         current_app.logger.error("Usuario Pedro Jose nao foi localizado no banco de dados. Execute o seed-dev.")
#         abort(404, description="Cenario de desenvolvimento nao inicializado.")

#     # 2. Extracao de relacionamentos via navegacao orientada a objetos (Lazy Loading)
#     # Recupera todos os vinculos ativos do usuario onde a data de termino e nula
#     active_associations = [
#         assoc for assoc in user.role_associations if assoc.finished_at is None
#     ]

#     # 3. Construcao do dicionario de promocao legado
#     promocao_vigente = "Segunda e dia de Pizza em dobro!!!"

#     # 4. Injecao de contexto enriquecido para a camada de visualizacao (Frontend)
#     return render_template(
#         'main/index.html',
#         user=user,
#         enderecos=user.addresses,
#         vinculos=active_associations,
#         promocao=promocao_vigente
#     )

# @bp_main.route('/carrinho')
# def carrinho():
#     carrinho = {
#         'itens': [
#             {'id': 1, 'name': "Pizza Margherita", 'preco': 49.95, 'quantidade': 1},
#             {'id': 2, 'name': "Refrigerante 2L", 'preco': 8.52, 'quantidade': 2},
#             {'id': 3, 'name': "Borda Recheada", 'preco': 12.358, 'quantidade': 1}
#         ]
#         #'itens': []
#     }
#     total = sum(item['preco']*item['quantidade'] for item  in carrinho['itens'])
#     return render_template('main/carrinho.html',
#                            carrinho=carrinho,
#                            total=total,
#                            titulo="Meu pedido prefido")


# @bp_main.route('/contato', methods=['GET', 'POST'])
# def contato():
#     form = ContatoForm()

#     if form.validate_on_submit():
#         current_app.logger.info(f"Mensagem recebida do {form.nome.data}")
#         flash('Mensagem enviada com sucesso!', 'success')
#         return redirect(url_for('main.index'))
#     else:
#         print(form.errors)

#     return render_template('main/contato.html', form=form)
