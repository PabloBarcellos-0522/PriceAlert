import pytest
from delivery import create_app


# =============================================================================
# FIXTURES (infraestrutura de teste)
# =============================================================================

@pytest.fixture
def app():
    """
    Cria uma instancia da aplicacao configurada para testes.
    """
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "test-key",
        "WTF_CSRF_ENABLED": False,
    })


@pytest.fixture
def client(app):
    """
    Cliente HTTP de teste (simula requisicoes sem servidor real).
    """
    return app.test_client()


# =============================================================================
# TESTES DE INFRAESTRUTURA
# =============================================================================

def test_app_is_created(app):
    """
    Verifica se a aplicacao foi criada corretamente.
    """
    assert app is not None


def test_config_is_loaded(app):
    """
    Garante que as configuracoes de teste foram aplicadas.
    """
    assert app.config["TESTING"] is True


def test_app_is_running_in_test_mode(app):
    """
    Confirma explicitamente o modo de execucao da aplicacao.
    """
    assert app.config["TESTING"] is True


# =============================================================================
# TESTES DE ROTAS
# =============================================================================

def test_non_existent_route_returns_404(client):
    """
    Rotas inexistentes devem retornar HTTP 404.
    """
    response = client.get("/url_que_nao_existe")
    assert response.status_code == 404


# -----------------------------------------------------------------------------
# TESTES PARAMETRIZADOS DE ROTAS PUBLICAS
# -----------------------------------------------------------------------------

PUBLIC_ROUTES = [
    ("/",         True),
    ("/contato",  True),
    ("/carrinho", True),
]


@pytest.mark.parametrize("route, check_doctype", PUBLIC_ROUTES)
def test_public_routes_return_200_in_html(client, route, check_doctype):
    """
    Verifica que rotas publicas:
    - retornam status 200
    - entregam HTML valido (verificacao minima)

    O uso de parametrizacao permite escalar facilmente os testes.
    """
    response = client.get(route)

    assert response.status_code == 200, \
        f"Rota {route} retornou {response.status_code}"

    assert (
        b"<html" in response.data or
        b"<!DOCTYPE html>" in response.data
    ), f"Rota {route} nao parece retornar HTML"

    if check_doctype:
        assert b"<!DOCTYPE html>" in response.data, \
            f"Rota {route} deveria conter DOCTYPE html"


# =============================================================================
# TESTES DE CONTEUDO
# =============================================================================

def test_index_page(client):
    """
    Verifica conteudo minimo da pagina inicial.
    """
    response = client.get('/')
    assert response.status_code == 200
    assert b"Delivery UVV" in response.data


# =============================================================================
# TESTES DE FORMULARIO
# =============================================================================

def test_contato_form(client):
    """
    Testa o fluxo completo de envio de formulario valido:
    - POST com dados corretos
    - espera redirecionamento (302)
    """
    response = client.post(
        '/contato',
        data={
            "nome": "Teste Aluno",
            "email": "teste@uvv.com",
            "mensagem": "Mensagem de teste para validacao",
            "submit": "Enviar Mensagem"
        },
        content_type="application/x-www-form-urlencoded"
    )

    assert response.status_code == 302  # redirect apos sucesso