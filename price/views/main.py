from flask import Blueprint, render_template, current_app, flash, redirect, url_for, request, abort, session, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal

from price.ext.db import db
from price.models.user import User
from price.models.product import Product
from price.models.product_monitoring import ProductMonitoring
from price.models.notification import Notification
from price.models.price_history import PriceHistory
from price.models.offer import Offer

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


@bp_main.context_processor
def inject_user_status():
    """Injeta o estado de login do usuário em todas as views do Blueprint."""
    return dict(usuario_logado='user_id' in session)


def check_password(user, password_candidate):
    """Compara senhas em hash ou plain text (para compatibilidade com seed de dev)."""
    try:
        if check_password_hash(user.password, password_candidate):
            return True
    except Exception:
        pass
    return user.password == password_candidate


@bp_main.route("/")
def index():
    usuario_logado = 'user_id' in session
    alertas = []
    historico = []

    if usuario_logado:
        user_id = session['user_id']
        notifications = Notification.query.filter_by(user_id=user_id).order_by(
            Notification.sent_at.desc()).limit(5).all()
        for n in notifications:
            best_offer = min(
                n.product.offers, key=lambda o: o.current_price) if n.product.offers else None
            monitoring = ProductMonitoring.query.filter_by(
                user_id=user_id, product_id=n.product_id).first()
            preco_alvo = float(monitoring.desired_price) if (
                monitoring and monitoring.desired_price) else 0.0
            alertas.append({
                "produto_nome": n.product.title,
                "preco_atual": float(best_offer.current_price) if best_offer else 0.0,
                "preco_alvo": preco_alvo,
                "data": n.sent_at,
                "url_produto": best_offer.product_url if best_offer else "#"
            })

        history_records = PriceHistory.query.join(Offer).join(Product).join(ProductMonitoring).filter(
            ProductMonitoring.user_id == user_id
        ).order_by(PriceHistory.captured_at.desc()).limit(5).all()
        for ph in history_records:
            preco_antigo = float(ph.price)
            preco_atual = float(ph.offer.current_price)
            variacao = ((preco_atual - preco_antigo) /
                        preco_antigo) * 100 if preco_antigo > 0 else 0
            historico.append({
                "produto_nome": ph.offer.product.title,
                "preco": preco_atual,
                "variacao": round(variacao, 2),
                "data": ph.captured_at
            })

    return render_template("main/index.html", usuario_logado=usuario_logado, alertas=alertas, historico=historico)


@bp_main.route("/dashboard")
def dashboard():
    usuario_logado = 'user_id' in session
    if not usuario_logado:
        flash("Acesse sua conta para ver o dashboard.", "info")
        return redirect(url_for("main.login"))

    user_id = session['user_id']
    total_monitorados = ProductMonitoring.query.filter_by(
        user_id=user_id, is_active=True).count()
    total_alertas = Notification.query.filter_by(user_id=user_id).count()

    economia_total = 0.0
    monitorings = ProductMonitoring.query.filter_by(
        user_id=user_id, is_active=True).all()
    total_lojas = 0
    for m in monitorings:
        offers_prices = [o.current_price for o in m.product.offers]
        total_lojas += len(offers_prices)
        if len(offers_prices) > 1:
            economia_total += float(max(offers_prices) - min(offers_prices))

    history_records = PriceHistory.query.join(Offer).join(Product).join(ProductMonitoring).filter(
        ProductMonitoring.user_id == user_id
    ).order_by(PriceHistory.captured_at.desc()).limit(10).all()

    ultimas_quedas = []
    for ph in history_records:
        preco_antigo = float(ph.price)
        preco_atual = float(ph.offer.current_price)
        if preco_atual < preco_antigo:
            variacao = ((preco_atual - preco_antigo) / preco_antigo) * 100
            ultimas_quedas.append({
                "produto_nome": ph.offer.product.title,
                "loja_nome": ph.offer.merchant,
                "preco_antigo": preco_antigo,
                "preco_atual": preco_atual,
                "variacao_percentual": round(variacao, 2),
                "data": ph.captured_at
            })

    return render_template(
        "main/dashboard.html",
        usuario_logado=True,
        total_monitorados=total_monitorados,
        total_alertas=total_alertas,
        economia_total=economia_total,
        total_lojas=total_lojas,
        ultimas_quedas=ultimas_quedas,
        monitoramentos_recentes=monitorings[:5]
    )


@bp_main.route("/search")
def search():
    usuario_logado = 'user_id' in session
    termo_busca = request.args.get("q", "").strip()
    forcar_api = request.args.get("forcar_api", "0") == "1"
    produtos = []
    fonte = None  # 'local' | 'api'

    if termo_busca:
        if not forcar_api:
            # 1) Busca no banco interno primeiro
            produtos_local = Product.query.filter(
                Product.title.ilike(f"%{termo_busca}%")
            ).order_by(Product.created_at.desc()).limit(30).all()

            if produtos_local:
                produtos = produtos_local
                fonte = 'local'

        if not produtos:
            # 2) Busca na API do SerpAPI (consome tokens)
            try:
                produtos = current_app.product_service.search(
                    termo_busca, fetch_offers=False)
                fonte = 'api'
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(
                    f"Erro ao buscar produtos via SerpAPI: {e}")
                flash("Ocorreu um erro na busca. Tente novamente.", "danger")

    return render_template(
        "main/search.html",
        usuario_logado=usuario_logado,
        termo_busca=termo_busca,
        produtos=produtos,
        fonte=fonte,
        forcar_api=forcar_api
    )


@bp_main.route("/monitored")
def monitored():
    usuario_logado = 'user_id' in session
    if not usuario_logado:
        flash("Acesse sua conta para ver seus alertas.", "info")
        return redirect(url_for("main.login"))

    produtos_monitorados = ProductMonitoring.query.filter_by(
        user_id=session['user_id'],
        is_active=True
    ).order_by(ProductMonitoring.created_at.desc()).all()

    return render_template(
        "main/monitored.html",
        usuario_logado=True,
        produtos_monitorados=produtos_monitorados
    )


@bp_main.route("/login", methods=["GET", "POST"])
def login():
    if 'user_id' in session:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password(user, form.senha.data):
            session['user_id'] = user.id
            flash(f"Bem-vindo de volta, {user.name}!", "success")
            return redirect(url_for("main.index"))
        else:
            flash("E-mail ou senha incorretos.", "danger")

    return render_template("main/login.html", form=form, usuario_logado=False)


@bp_main.route("/signup", methods=["GET", "POST"])
def signup():
    if 'user_id' in session:
        return redirect(url_for("main.index"))

    form = SignUpForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Este e-mail já está sendo utilizado.", "danger")
            return render_template("main/signup.html", form=form, usuario_logado=False)

        try:
            hashed_password = generate_password_hash(form.senha.data)
            new_user = User(
                name=form.nome.data,
                email=form.email.data,
                password=hashed_password
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Conta criada com sucesso! Faça seu login.", "success")

            current_app.email_service.send_welcome_email(new_user)
            return redirect(url_for("main.login"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao cadastrar usuário: {e}")
            flash("Ocorreu um erro ao criar a conta. Tente novamente.", "danger")

    return render_template("main/signup.html", form=form, usuario_logado=False)


@bp_main.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("main.index"))


@bp_main.route("/monitorados/adicionar", methods=["POST"])
def adicionar_monitoramento():
    if "user_id" not in session:
        flash("Você precisa estar logado para monitorar produtos.", "warning")
        return redirect(url_for("main.login"))

    user_id = session["user_id"]
    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        return redirect(url_for("main.login"))

    product_id = request.form.get("product_id")
    desired_price_raw = request.form.get("desired_price")

    product = db.session.get(Product, product_id)
    if not product:
        flash("Produto não encontrado.", "danger")
        return redirect(url_for("main.search"))

    current_app.price_scanner_service.update_single_product(product_id)

    desired_price = None
    if desired_price_raw:
        try:
            desired_price = Decimal(desired_price_raw)
        except Exception:
            flash("Preço alvo inválido.", "danger")
            return redirect(url_for("main.search"))

    try:
        current_app.monitoring_service.create_monitoring(
            user=user,
            product=product,
            desired_price=desired_price
        )

        flash(
            f"Produto '{product.title}' adicionado aos monitoramentos!", "success")
    except Exception as e:
        current_app.logger.error(f"Erro ao criar monitoramento: {e}")
        flash("Erro ao iniciar monitoramento.", "danger")

    return redirect(url_for("main.monitored"))


@bp_main.route("/monitorados/remover/<int:id>", methods=["POST"])
def remover_monitoramento(id):
    if "user_id" not in session:
        flash("Acesso não autorizado.", "warning")
        return redirect(url_for("main.login"))

    monitoring = db.session.get(ProductMonitoring, id)
    if not monitoring or monitoring.user_id != session["user_id"]:
        flash("Monitoramento não encontrado.", "danger")
        return redirect(url_for("main.monitored"))

    try:
        current_app.monitoring_service.stop_monitoring(monitoring)
        flash("Produto removido dos monitoramentos.", "success")
    except Exception as e:
        current_app.logger.error(f"Erro ao parar monitoramento: {e}")
        flash("Erro ao remover monitoramento.", "danger")

    return redirect(url_for("main.monitored"))


@bp_main.route("/api/offer/<int:offer_id>/price-history")
def offer_price_history(offer_id):
    """Retorna o histórico de preços de uma oferta específica em JSON."""
    if "user_id" not in session:
        return jsonify({"error": "Não autorizado"}), 401

    user_id = session["user_id"]

    # Verifica se a oferta pertence a um produto monitorado pelo usuário
    offer = (
        Offer.query
        .join(Product)
        .join(ProductMonitoring, ProductMonitoring.product_id == Product.id)
        .filter(
            Offer.id == offer_id,
            ProductMonitoring.user_id == user_id,
            ProductMonitoring.is_active == True
        )
        .first()
    )

    if not offer:
        return jsonify({"error": "Oferta não encontrada"}), 404

    history = (
        PriceHistory.query
        .filter_by(offer_id=offer_id)
        .order_by(PriceHistory.captured_at.asc())
        .all()
    )

    # Inclui o preço atual como ponto mais recente
    points = [
        {
            "date": ph.captured_at.strftime("%d/%m/%Y %H:%M"),
            "price": float(ph.price)
        }
        for ph in history
    ]

    # Adiciona o preço corrente como último ponto se não houver histórico
    # ou se o histórico existir mas o último ponto for diferente do atual
    if not points or float(offer.current_price) != points[-1]["price"]:
        from datetime import datetime
        points.append({
            "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "price": float(offer.current_price)
        })

    return jsonify({
        "merchant": offer.merchant,
        "current_price": float(offer.current_price),
        "history": points
    })
