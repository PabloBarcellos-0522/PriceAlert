from price.models.notification import Notification
from price.models.price_history import PriceHistory
from price.models.product_monitoring import ProductMonitoring
from price.models.offer import Offer
from price.models.product import Product
from price.models.user import User
from price.ext.db import db as _db
from price import create_app
import os
import pytest
from decimal import Decimal
from unittest.mock import MagicMock

# Define test environment variables before importing anything to avoid Configuration / KeyError issues
os.environ["APP_ENV"] = "testing"
os.environ["TESTING"] = "True"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["WTF_CSRF_ENABLED"] = "False"
os.environ["SERPAPI_API_KEY"] = "test-serpapi-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["MAIL_DEFAULT_SENDER"] = "noreply@pricealert.com"
TESTING = True
MAIL_SUPPRESS_SEND = True


@pytest.fixture(scope="session")
def app():
    """Cria e configura o app Flask para testes."""
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "MAIL_SUPPRESS_SEND": True,
    })
    return app


@pytest.fixture(scope="function")
def db(app):
    """Cria as tabelas do banco de dados para cada teste."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    """Cliente HTTP de teste."""
    return app.test_client()


@pytest.fixture(scope="function")
def test_user(db):
    """Usuário padrão para testes."""
    from werkzeug.security import generate_password_hash
    user = User(
        name="Teste Usuário",
        email="pablobarcellossoares@gmail.com",
        password=generate_password_hash("senha123")
    )
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture(scope="function")
def logged_in_client(client, test_user):
    """Cliente HTTP de teste já autenticado."""
    with client.session_transaction() as sess:
        sess['user_id'] = test_user.id
    return client


@pytest.fixture(scope="function")
def test_product(db):
    """Produto padrão para testes."""
    product = Product(
        google_product_id="prod_123",
        title="Celular Incrível",
        str_current_price="R$ 1.500,00",
        rating=4,
        review_count=10,
        product_token="token_xyz",
        product_shoping_link="http://shopping.com/123",
        image="http://shopping.com/image.jpg"
    )
    _db.session.add(product)
    _db.session.commit()
    return product


@pytest.fixture(scope="function")
def test_offer(db, test_product):
    """Oferta padrão para testes."""
    offer = Offer(
        product=test_product,
        merchant="Magazine Teste",
        product_url="http://magazineteste.com/prod",
        current_price=Decimal("1500.00"),
        shipping_price=Decimal("15.00"),
        rating=5,
        reviews_count=2
    )
    _db.session.add(offer)
    _db.session.commit()
    return offer


@pytest.fixture(scope="function")
def mock_serpapi_service(app):
    """Mock do serviço do SerpAPI para evitar chamadas de rede."""
    mock = MagicMock()
    app.serpapi_service = mock
    return mock
