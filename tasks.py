from invoke import task
from datetime import datetime
from dotenv import load_dotenv
import os
import zipfile


# ==========================================================
# GERENCIAMENTO DE AMBIENTE
# ==========================================================
def load_env(env: str):
    """
    Carrega o arquivo .env correspondente ao ambiente.
    Ex: dev, test, prod
    """
    env_file = f".env.{env}"

    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
        print(f"[ENV] Carregado: {env_file}")
    else:
        raise FileNotFoundError(f"{env_file} nao encontrado")


# ==========================================================
# INSTALACAO
# ==========================================================

# .\venv\Scripts\activate para acessar o venv
# source ./venv/Scripts/activate para linux
# invoke install para iniciar
@task
def install(c, dev=True):
    """
    Instala o projeto.
    """
    if dev:
        c.run('pip install -e ".[dev,test]"', echo=True)
    else:
        # invoke install --no-dev
        c.run("pip install .", echo=True)


@task
def uninstall(c):
    """
    Remove o pacote instalado.
    """
    c.run("pip uninstall -y price", echo=True)


# ==========================================================
# EXECUCAO
# ==========================================================
@task
def run(c):
    """
    Executa a aplicacao Flask em ambiente de desenvolvimento.
    """
    load_env("dev")
    c.run("flask run")


@task
def prod(c):
    """
    Executa a aplicacao em modo producao.
    """
    load_env("prod")
    c.run("flask run")


# ==========================================================
# TESTES
# ==========================================================
@task
def test(c):
    """
    Executa os testes automatizados.
    """
    load_env("test")
    c.run("pytest -v", env={"PYTHONPATH": "."})


# ==========================================================
# QUALIDADE DE CODIGO
# ==========================================================
@task
def lint(c):
    """
    Verifica qualidade de codigo.
    """
    c.run("flake8")


@task
def format(c):
    """
    Formata o codigo automaticamente.
    """
    c.run("black .")


# flask create-db
@task
def create_db(c):
    """
    Executa o comando de create_db
    """
    load_env("dev")
    c.run("flask create-db")


@task
def seed_dev(c):
    """
    Executa o comando de seed garantindo o ambiente de desenvolvimento.
    """
    load_env("dev")
    c.run("flask seed-dev")


@task
def drop_db(c):
    """
    Executa o comando de drop_db garantindo o ambiente de desenvolvimento.
    """
    load_env("dev")
    c.run("flask drop-db")


@task
def prod_create_db(c):
    """
    Executa o comando de create_db
    """
    load_env("prod")
    c.run("flask create-db")


@task
def prod_drop_db(c):
    """
    Executa o comando de drop_db garantindo o ambiente de desenvolvimento.
    """
    load_env("prod")
    c.run("flask drop-db")

# ==========================================================
# EMPACOTAMENTO
# ==========================================================


@task
def zip(c, name=None):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    zip_filename = name or f"price-projeto-{timestamp}.zip"
    zip_path = os.path.abspath(os.path.join("..", zip_filename))

    print(f"→ Criando ZIP: {zip_path}")

    excludes = [
        "venv",
        "__pycache__",
        ".git",
        ".vscode",
        "price.egg-info"
    ]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):

            dirs[:] = [d for d in dirs if d not in excludes]

            for file in files:
                if file.endswith((".pyc", ".pyo", ".pyd", ".log", ".db", ".sqlite3")):
                    continue

                filepath = os.path.join(root, file)
                zipf.write(filepath)

    if os.path.exists(zip_path):
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"→ ZIP criado com sucesso: {zip_path}")
        print(f"   Tamanho: {size_mb:.2f} MB")
