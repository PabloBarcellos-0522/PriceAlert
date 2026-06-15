import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from price.ext.db import db
from price.models.product import Product
from price.models.product_monitoring import ProductMonitoring
from price.models.notification import Notification


# =============================================================================
# FIXTURES LOCAIS PARA OS TESTES DO SCANNER
# =============================================================================

@pytest.fixture
def active_monitoring(db, test_user, test_product):
    """Cria e retorna um monitoramento ativo."""
    monitoring = ProductMonitoring(
        user=test_user,
        product=test_product,
        desired_price=Decimal("1400.00"),
        is_active=True
    )
    db.session.add(monitoring)
    db.session.commit()
    return monitoring


# =============================================================================
# TESTES DE PRICESCANNER_SERVICE
# =============================================================================

def test_price_scanner_service_no_active_products(app, db):
    """Testa se scan_all_active_prices retorna cedo sem escanear se não houver produtos ativos."""
    service = app.price_scanner_service

    # Garante que não há monitoramentos ativos
    db.session.query(ProductMonitoring).update(
        {ProductMonitoring.is_active: False})
    db.session.commit()

    mock_get_details = MagicMock()
    mock_check = MagicMock(return_value=[])
    mock_send_batch = MagicMock()

    with patch.object(app.product_service, 'get_product_details', mock_get_details), \
            patch.object(app.monitoring_service, 'check_all_active_monitorings', mock_check), \
            patch.object(app.email_service, 'send_notifications_batch', mock_send_batch):

        with app.app_context():
            service.scan_all_active_prices()

        mock_get_details.assert_not_called()
        mock_check.assert_not_called()
        mock_send_batch.assert_not_called()


def test_price_scanner_service_success_flow(app, db, test_user, test_product, active_monitoring):
    """Testa o fluxo completo de sucesso do scan_all_active_prices."""
    service = app.price_scanner_service

    mock_get_details = MagicMock()
    mock_notification = Notification(
        user=test_user,
        product=test_product,
        title="Alerta de Preço!",
        message="Preço caiu!"
    )
    db.session.add(mock_notification)
    mock_check = MagicMock(return_value=[mock_notification])
    mock_send_batch = MagicMock(return_value={"sent": 1, "failed": 0})

    with patch.object(app.product_service, 'get_product_details', mock_get_details) as get_details_mock, \
            patch.object(app.monitoring_service, 'check_all_active_monitorings', mock_check) as check_mock, \
            patch.object(app.email_service, 'send_notifications_batch', mock_send_batch) as send_mock:

        with app.app_context():
            service.scan_all_active_prices()

        get_details_mock.assert_called_once_with(
            page_token=test_product.product_token, commit=False)
        check_mock.assert_called_once()
        send_mock.assert_called_once_with([mock_notification])


def test_price_scanner_service_product_without_token(app, db, test_user, active_monitoring):
    """Testa se scan_all_active_prices ignora a chamada SerpAPI de um produto sem token e continua."""
    service = app.price_scanner_service

    # Remove token do produto monitorado ativo
    active_monitoring.product.product_token = None
    db.session.commit()

    mock_get_details = MagicMock()
    mock_check = MagicMock(return_value=[])

    with patch.object(app.product_service, 'get_product_details', mock_get_details) as get_details_mock, \
            patch.object(app.monitoring_service, 'check_all_active_monitorings', mock_check) as check_mock:

        with app.app_context():
            service.scan_all_active_prices()

        get_details_mock.assert_not_called()
        check_mock.assert_called_once()


def test_price_scanner_service_partial_failure(app, db, test_user):
    """Testa se falhas individuais ao obter detalhes de um produto não impedem a execução para outros."""
    service = app.price_scanner_service

    # Criar 2 produtos e monitoramentos ativos
    p1 = Product(google_product_id="prod_1",
                 title="Prod 1", product_token="token_1")
    p2 = Product(google_product_id="prod_2",
                 title="Prod 2", product_token="token_2")
    db.session.add_all([p1, p2])
    db.session.commit()

    m1 = ProductMonitoring(user=test_user, product=p1,
                           desired_price=Decimal("100"), is_active=True)
    m2 = ProductMonitoring(user=test_user, product=p2,
                           desired_price=Decimal("100"), is_active=True)
    db.session.add_all([m1, m2])
    db.session.commit()

    # Primeiro token falha, o segundo funciona
    def side_effect(page_token, commit=False):
        if page_token == "token_1":
            raise Exception("Erro na API")
        return {"product": p2, "offers": []}

    mock_get_details = MagicMock(side_effect=side_effect)
    mock_check = MagicMock(return_value=[])

    with patch.object(app.product_service, 'get_product_details', mock_get_details), \
            patch.object(app.monitoring_service, 'check_all_active_monitorings', mock_check):

        with app.app_context():
            service.scan_all_active_prices()

    assert mock_get_details.call_count == 2
    mock_check.assert_called_once()


def test_price_scanner_service_critical_failure(app, db, test_user, active_monitoring):
    """Testa o tratamento de falha crítica (ex: banco de dados inacessível) disparando rollback."""
    service = app.price_scanner_service

    mock_get_details = MagicMock()

    with patch.object(app.product_service, 'get_product_details', mock_get_details), \
            patch.object(db.session, 'commit', side_effect=Exception("Perda de conexao")) as mock_commit, \
            patch.object(db.session, 'rollback') as mock_rollback:

        with app.app_context():
            service.scan_all_active_prices()

        mock_commit.assert_called_once()
        mock_rollback.assert_called_once()


def test_update_single_product_success(app, db, test_product):
    """Testa atualização de preço individual com sucesso."""
    service = app.price_scanner_service
    mock_get_details = MagicMock()

    with patch.object(app.product_service, 'get_product_details', mock_get_details) as get_details_mock:
        with app.app_context():
            result = service.update_single_product(test_product.id)

        assert result == {"success": True, "product_id": test_product.id}
        get_details_mock.assert_called_once_with(
            page_token=test_product.product_token, commit=False)


def test_update_single_product_not_found(app, db):
    """Testa atualização de preço individual quando produto não existe."""
    service = app.price_scanner_service

    with app.app_context():
        result = service.update_single_product(99999)

    assert result == {"success": False, "error": "Produto não encontrado"}


def test_update_single_product_exception(app, db, test_product):
    """Testa tratamento de exceções na atualização de preço individual."""
    service = app.price_scanner_service
    mock_get_details = MagicMock(side_effect=Exception("Erro inesperado"))

    with patch.object(app.product_service, 'get_product_details', mock_get_details), \
            patch.object(db.session, 'rollback') as mock_rollback:
        with app.app_context():
            result = service.update_single_product(test_product.id)

        assert result["success"] is False
        assert "Erro inesperado" in result["error"]
        mock_rollback.assert_called_once()
