import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock
from flask import session, url_for
from price.ext.db import db
from price.models.user import User
from price.models.product import Product
from price.models.offer import Offer
from price.models.product_monitoring import ProductMonitoring
from price.models.price_history import PriceHistory
from price.models.notification import Notification

# =============================================================================
# 1. TESTES DE MODELOS E BANCO DE DADOS
# =============================================================================


def test_user_model(test_user):
    """Testa atributos e repr do modelo User."""
    assert test_user.id is not None
    assert test_user.name == "Teste Usuário"
    assert test_user.email == "pablobarcellossoares@gmail.com"
    assert "pablobarcellossoares@gmail.com" in repr(test_user)
    assert test_user.is_active is True


def test_product_model(test_product, test_offer):
    """Testa propriedades calculadas do modelo Product."""
    assert test_product.nome == "Celular Incrível"
    assert test_product.imagem_url == "http://shopping.com/image.jpg"
    assert test_product.preco_atual == 1500.0
    assert test_product.loja_nome == "Magazine Teste"

    # Teste de preco_atual e loja_nome sem ofertas
    product_no_offers = Product(
        google_product_id="prod_empty",
        title="Sem Ofertas",
        str_current_price="R$ 0,00",
        product_token="token_empty",
        product_shoping_link="http://shopping.com/empty",
        image=""
    )
    db.session.add(product_no_offers)
    db.session.commit()
    assert product_no_offers.preco_atual == 0.0
    assert product_no_offers.loja_nome == "N/A"


def test_offer_model(test_offer, test_product):
    """Testa atributos e relacionamentos do modelo Offer."""
    assert test_offer.id is not None
    assert test_offer.merchant == "Magazine Teste"
    assert test_offer.current_price == Decimal("1500.00")
    assert test_offer.product_id == test_product.id
    assert test_offer.product == test_product


def test_price_history_model(db, test_offer):
    """Testa o modelo PriceHistory."""
    history = PriceHistory(
        offer=test_offer,
        price=Decimal("1400.00")
    )
    db.session.add(history)
    db.session.commit()

    assert history.id is not None
    assert history.offer_id == test_offer.id
    assert history.price == Decimal("1400.00")
    assert history.captured_at is not None


def test_product_monitoring_model(db, test_user, test_product, test_offer):
    """Testa propriedades calculadas do modelo ProductMonitoring."""
    monitoring = ProductMonitoring(
        user=test_user,
        product=test_product,
        desired_price=Decimal("1200.00"),
        is_active=True
    )
    db.session.add(monitoring)
    db.session.commit()

    assert monitoring.nome == "Celular Incrível"
    assert monitoring.imagem_url == "http://shopping.com/image.jpg"
    assert monitoring.preco_atual == 1500.0
    assert monitoring.loja_nome == "Magazine Teste"
    assert monitoring.preco_alvo == 1200.0

    # Sem produto
    monitoring_no_prod = ProductMonitoring(user=test_user, product=None)
    assert monitoring_no_prod.nome == ""
    assert monitoring_no_prod.imagem_url == ""
    assert monitoring_no_prod.preco_atual == 0.0
    assert monitoring_no_prod.loja_nome == "N/A"


def test_notification_model(db, test_user, test_product):
    """Testa atributos do modelo Notification."""
    notification = Notification(
        user=test_user,
        product=test_product,
        title="Alerta!",
        message="O preço baixou."
    )
    db.session.add(notification)
    db.session.commit()

    assert notification.id is not None
    assert notification.user_id == test_user.id
    assert notification.product_id == test_product.id
    assert notification.title == "Alerta!"
    assert notification.message == "O preço baixou."
    assert notification.sent_at is not None


# =============================================================================
# 2. TESTES DOS SERVIÇOS (SERVICES)
# =============================================================================

# -----------------------------------------------------------------------------
# 2.1 MonitoringService
# -----------------------------------------------------------------------------

def test_monitoring_service_create_monitoring(app, db, test_user, test_product):
    """Testa criação de monitoramento pelo MonitoringService."""
    service = app.monitoring_service

    # Criação inicial
    m1 = service.create_monitoring(
        user=test_user,
        product=test_product,
        desired_price=Decimal("1000.00"),
        notify_only_lowest_price=True
    )
    assert m1.id is not None
    assert m1.user_id == test_user.id
    assert m1.product_id == test_product.id
    assert m1.desired_price == Decimal("1000.00")
    assert m1.notify_only_lowest_price is True
    assert m1.is_active is True

    # Re-criar monitoramento idêntico ativo (deve retornar o mesmo)
    m2 = service.create_monitoring(
        user=test_user,
        product=test_product,
        desired_price=Decimal("900.00")
    )
    assert m2.id == m1.id
    # Não deve alterar valores de monitoramento que já está ativo
    assert m2.desired_price == Decimal("1000.00")

    # Parar monitoramento
    service.stop_monitoring(m1)
    assert m1.is_active is False

    # Re-criar monitoramento inativo (deve ativar e atualizar parâmetros)
    m3 = service.create_monitoring(
        user=test_user,
        product=test_product,
        desired_price=Decimal("800.00"),
        notify_only_lowest_price=False
    )
    assert m3.id == m1.id
    assert m3.is_active is True
    assert m3.desired_price == Decimal("800.00")
    assert m3.notify_only_lowest_price is False


def test_monitoring_service_check_and_notify_desired_price(app, db, test_user, test_product, test_offer):
    """Testa as notificações com base no preço alvo desejado."""
    service = app.monitoring_service

    # Monitoramento com preço desejado de R$ 1600 (preço atual é R$ 1500, logo deve notificar)
    m = service.create_monitoring(
        user=test_user,
        product=test_product,
        desired_price=Decimal("1600.00")
    )

    notifications = service.check_and_notify(m)
    assert len(notifications) == 1
    assert notifications[0].title == "Preço alvo atingido! 🎯"
    assert "Magazine Teste" in notifications[0].message
    assert m.last_notified_price == Decimal("1500.00")

    # Verifica se não notifica novamente se o preço continuar o mesmo
    notifications_dup = service.check_and_notify(m)
    assert len(notifications_dup) == 0

    # Altera preço atual para R$ 1400 (abaixo do último notificado, deve notificar de novo)
    test_offer.current_price = Decimal("1400.00")
    db.session.commit()

    notifications_lower = service.check_and_notify(m)
    assert len(notifications_lower) == 1
    assert m.last_notified_price == Decimal("1400.00")

    # Altera preço atual para R$ 1450 (subiu, não deve notificar)
    test_offer.current_price = Decimal("1450.00")
    db.session.commit()
    notifications_higher = service.check_and_notify(m)
    assert len(notifications_higher) == 0


def test_monitoring_service_check_and_notify_lowest_price(app, db, test_user, test_product, test_offer):
    """Testa as notificações com base no menor preço histórico."""
    service = app.monitoring_service

    # Monitoramento com menor preço histórico
    m = service.create_monitoring(
        user=test_user,
        product=test_product,
        desired_price=None,
        notify_only_lowest_price=True
    )

    # Preço atual é R$ 1500. Histórico está vazio. Como não está abaixo de histórico, não deve notificar.
    notifications1 = service.check_and_notify(m)
    assert len(notifications1) == 0

    # Adiciona um histórico de R$ 1500. E baixa o preço atual para R$ 1300.
    ph = PriceHistory(offer=test_offer, price=Decimal("1500.00"))
    db.session.add(ph)
    test_offer.current_price = Decimal("1300.00")
    db.session.commit()

    # Agora o preço atual (1300) é menor que o histórico mínimo (1500), deve notificar!
    notifications2 = service.check_and_notify(m)
    assert len(notifications2) == 1
    assert notifications2[0].title == "Menor preço registrado! 💰"
    assert m.last_notified_price == Decimal("1300.00")


def test_monitoring_service_queries(app, db, test_user, test_product):
    """Testa métodos de consulta do MonitoringService."""
    service = app.monitoring_service

    m = service.create_monitoring(user=test_user, product=test_product)

    # Adiciona notificação manual
    notification = Notification(
        user=test_user, product=test_product, title="T", message="M")
    db.session.add(notification)
    db.session.commit()

    # Query monitorings
    monitorings_active = service.get_user_monitorings(
        test_user, active_only=True)
    assert len(monitorings_active) == 1
    assert monitorings_active[0].id == m.id

    service.stop_monitoring(m)
    assert len(service.get_user_monitorings(test_user, active_only=True)) == 0
    assert len(service.get_user_monitorings(test_user, active_only=False)) == 1

    # Query notifications
    notifications = service.get_user_notifications(test_user)
    assert len(notifications) == 1
    assert notifications[0].title == "T"

# -----------------------------------------------------------------------------
# 2.2 EmailService
# -----------------------------------------------------------------------------


def test_email_service_send_welcome_email(app, test_user):
    """Testa envio de email de boas vindas."""
    service = app.email_service

    # Com Flask-Mail, em modo TESTING=True, o envio é suprimido mas as mensagens são gravadas no outbox
    with app.mail.record_messages() as outbox:
        success = service.send_welcome_email(test_user)
        assert success is True
        assert len(outbox) == 1
        msg = outbox[0]
        assert msg.subject == "Bem-vindo ao PriceAlert! 🎉"
        assert msg.recipients == ["pablobarcellossoares@gmail.com"]
        assert "Olá Teste Usuário" in msg.html


def test_email_service_send_notification_email(app, test_user, test_product):
    """Testa envio de email de notificação."""
    service = app.email_service
    notification = Notification(
        user=test_user,
        product=test_product,
        title="Preço Alvo Atingido!",
        message="O produto Celular Incrível atingiu seu preço alvo."
    )
    db.session.add(notification)
    db.session.commit()

    with app.mail.record_messages() as outbox:
        success = service.send_notification_email(notification)
        assert success is True
        assert len(outbox) == 1
        msg = outbox[0]
        assert msg.subject == "Preço Alvo Atingido!"
        assert msg.recipients == ["pablobarcellossoares@gmail.com"]
        assert "Celular Incrível" in msg.html


def test_email_service_send_notifications_batch(app, test_user, test_product):
    """Testa envio de notificações em lote."""
    service = app.email_service
    n1 = Notification(id=1, user=test_user,
                      product=test_product, title="T1", message="M1")
    n2 = Notification(id=2, user=test_user,
                      product=test_product, title="T2", message="M2")
    db.session.add_all([n1, n2])
    db.session.commit()

    with app.mail.record_messages() as outbox:
        results = service.send_notifications_batch([n1, n2])
        assert results["total"] == 2
        assert results["sent"] == 2
        assert results["failed"] == 0
        assert len(outbox) == 2


def test_email_service_send_daily_digest(app, test_user, test_product):
    """Testa envio de digest diário."""
    service = app.email_service
    n1 = Notification(user=test_user, product=test_product,
                      title="Alerta 1", message="M1", sent_at=datetime.now())
    n2 = Notification(user=test_user, product=test_product,
                      title="Alerta 2", message="M2", sent_at=datetime.now())
    db.session.add_all([n1, n2])
    db.session.commit()

    with app.mail.record_messages() as outbox:
        success = service.send_daily_digest(test_user, [n1, n2])
        assert success is True
        assert len(outbox) == 1
        msg = outbox[0]
        assert "Resumo do dia" in msg.subject
        assert "Alerta 1" in msg.html
        assert "Alerta 2" in msg.html

# -----------------------------------------------------------------------------
# 2.3 SerpapiProductService
# -----------------------------------------------------------------------------


def test_serpapi_product_service_search(app, db, mock_serpapi_service):
    """Testa busca de produtos através do SerpapiProductService."""
    service = app.product_service

    # Mock da resposta do SerpAPI
    mock_serpapi_service.search.return_value = {
        "shopping_results": [
            {
                "product_id": "api_prod_999",
                "title": "Fone de Ouvido Bluetooth",
                "price": "R$ 299,00",
                "rating": 5,
                "reviews": 15,
                "immersive_product_page_token": "token_fone_999",
                "product_link": "http://link.com/fone",
                "thumbnail": "http://img.com/fone.jpg"
            }
        ]
    }

    with app.app_context():
        products = service.search("fone de ouvido", fetch_offers=False)
        assert len(products) == 1
        p = products[0]
        assert p.google_product_id == "api_prod_999"
        assert p.title == "Fone de Ouvido Bluetooth"
        assert p.str_current_price == "R$ 299,00"
        assert p.rating == 5
        assert p.review_count == 15
        assert p.product_token == "token_fone_999"

        # Verifica persistência no banco
        db_product = Product.query.filter_by(
            google_product_id="api_prod_999").first()
        assert db_product is not None
        assert db_product.id == p.id


def test_serpapi_product_service_get_product_details(app, db, mock_serpapi_service, test_product):
    """Testa detalhamento de produto e criação/atualização de ofertas/histórico."""
    service = app.product_service

    # Mock da resposta de detalhes do produto
    mock_serpapi_service.get_product_details.return_value = {
        "product_results": {
            "product_id": test_product.google_product_id,
            "title": test_product.title,
            "price": "R$ 1.500,00",
            "stores": [
                {
                    "name": "Loja Barata",
                    "link": "http://lojabarata.com/celular",
                    "extracted_price": 1450.00,
                    "shipping": 10.00,
                    "rating": 4,
                    "reviews": 8
                }
            ]
        }
    }

    with app.app_context():
        # Busca detalhes que devem criar a oferta Loja Barata
        res = service.get_product_details("token_xyz", commit=True)
        assert res["product"].id == test_product.id
        assert len(res["offers"]) == 1

        offer = res["offers"][0]
        assert offer.merchant == "Loja Barata"
        assert offer.current_price == Decimal("1450.00")
        assert offer.shipping_price == Decimal("10.00")

        # Agora mocka um preço menor para gerar histórico de preços
        mock_serpapi_service.get_product_details.return_value[
            "product_results"]["stores"][0]["extracted_price"] = 1400.00

        res2 = service.get_product_details("token_xyz", commit=True)
        assert len(res2["offers"]) == 1
        updated_offer = res2["offers"][0]
        assert updated_offer.current_price == Decimal("1400.00")

        # Deve ter criado um registro no histórico de preços com o valor antigo (1450.00)
        history = PriceHistory.query.filter_by(offer_id=updated_offer.id).all()
        assert len(history) == 1
        assert history[0].price == Decimal("1450.00")


# =============================================================================
# 3. TESTES DE ROTEAMENTO, SESSÃO E RENDERIZAÇÃO DE PÁGINAS
# =============================================================================

# -----------------------------------------------------------------------------
# 3.1 Rotas Públicas
# -----------------------------------------------------------------------------

def test_index_page_anonymous(client):
    """Página inicial deve renderizar para usuários anônimos."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "PriceAlert" in html
    assert "Entrar" in html


def test_login_page_renders(client):
    """Página de Login deve renderizar formulário de entrada."""
    response = client.get("/login")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Entrar" in html
    assert "E-mail" in html


def test_signup_page_renders(client):
    """Página de Cadastro deve renderizar formulário de cadastro."""
    response = client.get("/signup")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Criar Conta" in html
    assert "Nome Completo" in html

# -----------------------------------------------------------------------------
# 3.2 Fluxo de Autenticação e Cadastro
# -----------------------------------------------------------------------------


def test_signup_flow(client, db):
    """Testa cadastro de novo usuário com dados válidos e duplicados."""
    # Envia dados válidos
    response = client.post(
        "/signup",
        data={
            "nome": "Novo Aluno",
            "email": "novo@teste.com",
            "senha": "senha",
            "confirmar_senha": "senha",
            "submit": "Criar Conta"
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "Conta criada com sucesso" in response.get_data(as_text=True)

    # Verifica se persistiu no banco
    u = User.query.filter_by(email="novo@teste.com").first()
    assert u is not None
    assert u.name == "Novo Aluno"

    # Tenta cadastrar novamente com o mesmo e-mail (deve acusar erro)
    response_dup = client.post(
        "/signup",
        data={
            "nome": "Outro Nome",
            "email": "novo@teste.com",
            "senha": "senha",
            "confirmar_senha": "senha",
            "submit": "Criar Conta"
        },
        follow_redirects=True
    )
    assert "Este e-mail já está sendo utilizado" in response_dup.get_data(
        as_text=True)


def test_login_logout_flow(client, test_user):
    """Testa login com credenciais válidas/inválidas e logout."""
    # Login inválido
    response_invalid = client.post(
        "/login",
        data={"email": "pablobarcellossoares@gmail.com",
              "senha": "senha_errada", "submit": "Entrar"},
        follow_redirects=True
    )
    assert "E-mail ou senha incorretos" in response_invalid.get_data(
        as_text=True)

    # Login válido
    response_valid = client.post(
        "/login",
        data={"email": "pablobarcellossoares@gmail.com",
              "senha": "senha123", "submit": "Entrar"},
        follow_redirects=True
    )
    assert "Bem-vindo de volta" in response_valid.get_data(as_text=True)

    # Logout
    response_logout = client.get("/logout", follow_redirects=True)
    assert "Você saiu da sua conta" in response_logout.get_data(as_text=True)

# -----------------------------------------------------------------------------
# 3.3 Acesso a Rotas Protegidas e Operações de Monitoramento
# -----------------------------------------------------------------------------


def test_protected_routes_redirect_to_login(client):
    """Verifica redirecionamento de anônimos acessando rotas protegidas."""
    for route in ["/dashboard", "/monitored"]:
        response = client.get(route)
        assert response.status_code == 302
        assert "/login" in response.location


def test_dashboard_page_authenticated(logged_in_client, db, test_user, test_product, test_offer):
    """Testa renderização do dashboard para usuário logado."""
    # Adiciona monitoramento ativo
    m = ProductMonitoring(user=test_user, product=test_product, is_active=True)
    db.session.add(m)
    db.session.commit()

    response = logged_in_client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Dashboard" in html
    assert "Celular Incrível" in html


def test_monitored_page_authenticated(logged_in_client, db, test_user, test_product, test_offer):
    """Testa renderização dos produtos monitorados para usuário logado."""
    m = ProductMonitoring(user=test_user, product=test_product,
                          desired_price=Decimal("1300.00"), is_active=True)
    db.session.add(m)
    db.session.commit()

    response = logged_in_client.get("/monitored")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Produtos Monitorados" in html
    assert "Celular Incrível" in html
    assert "Alvo: R$ 1300.00" in html
    assert "Magazine Teste" in html
    assert "Histórico" in html


def test_adicionar_monitoramento_flow(logged_in_client, db, test_product):
    """Testa a rota de adicionar monitoramento."""
    response = logged_in_client.post(
        "/monitorados/adicionar",
        data={"product_id": test_product.id, "desired_price": "1400.00"},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "adicionado aos monitoramentos" in response.get_data(as_text=True)

    # Verifica banco de dados
    m = ProductMonitoring.query.filter_by(product_id=test_product.id).first()
    assert m is not None
    assert m.desired_price == Decimal("1400.00")
    assert m.is_active is True


def test_remover_monitoramento_flow(logged_in_client, db, test_user, test_product):
    """Testa a rota de remoção/desativação de monitoramento."""
    m = ProductMonitoring(user=test_user, product=test_product, is_active=True)
    db.session.add(m)
    db.session.commit()

    response = logged_in_client.post(
        f"/monitorados/remover/{m.id}",
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "Produto removido dos monitoramentos" in response.get_data(
        as_text=True)

    # Verifica que não foi deletado, mas sim marcado como inativo
    m_db = db.session.get(ProductMonitoring, m.id)
    assert m_db.is_active is False

# -----------------------------------------------------------------------------
# 3.4 API de Histórico de Preços da Oferta
# -----------------------------------------------------------------------------


def test_api_offer_price_history_anonymous(client, test_offer):
    """Acesso à API sem estar logado deve retornar 401."""
    response = client.get(f"/api/offer/{test_offer.id}/price-history")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Não autorizado"


def test_api_offer_price_history_not_found(logged_in_client):
    """Acesso a oferta inexistente ou não monitorada deve retornar 404."""
    response = logged_in_client.get("/api/offer/99999/price-history")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Oferta não encontrada"


def test_api_offer_price_history_success(logged_in_client, db, test_user, test_product, test_offer):
    """Testa se a API de histórico retorna os dados corretos em JSON."""
    # Configura o monitoramento ativo para o usuário
    m = ProductMonitoring(user=test_user, product=test_product, is_active=True)
    db.session.add(m)

    # Adiciona histórico de preços
    ph1 = PriceHistory(offer=test_offer, price=Decimal(
        "1700.00"), captured_at=datetime(2026, 6, 1, 10, 0))
    ph2 = PriceHistory(offer=test_offer, price=Decimal(
        "1600.00"), captured_at=datetime(2026, 6, 5, 12, 0))
    db.session.add_all([ph1, ph2])
    db.session.commit()

    response = logged_in_client.get(
        f"/api/offer/{test_offer.id}/price-history")
    assert response.status_code == 200
    data = response.get_json()

    assert data["merchant"] == "Magazine Teste"
    assert data["current_price"] == 1500.0

    # Deve conter os pontos históricos + o preço atual (total 3 pontos)
    history = data["history"]
    assert len(history) == 3
    assert history[0]["price"] == 1700.0
    assert history[0]["date"] == "01/06/2026 10:00"
    assert history[1]["price"] == 1600.0
    assert history[1]["date"] == "05/06/2026 12:00"
    assert history[2]["price"] == 1500.0
