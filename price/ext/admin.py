"""
Extensão Flask-Admin para gerenciamento do banco de dados.
Acessível em /admin apenas para usuários logados.
"""

from flask import redirect, url_for, session
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView

from price.ext.db import db
from price.models.user import User
from price.models.product import Product
from price.models.offer import Offer
from price.models.price_history import PriceHistory
from price.models.product_monitoring import ProductMonitoring
from price.models.notification import Notification


class AdminSecureMixin:
    """Protege todas as views do admin para usuários logados."""

    def is_accessible(self):
        return 'user_id' in session

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.login'))


class AdminHomeView(AdminSecureMixin, AdminIndexView):
    @expose('/')
    def index(self):
        if not self.is_accessible():
            return self.inaccessible_callback('index')

        # Estatísticas para a página inicial do admin
        stats = {
            'total_usuarios': User.query.count(),
            'total_produtos': Product.query.count(),
            'total_ofertas': Offer.query.count(),
            'total_historico': PriceHistory.query.count(),
            'total_monitoramentos': ProductMonitoring.query.count(),
            'total_notificacoes': Notification.query.count(),
        }
        return self.render('admin/index.html', stats=stats)


class SecureModelView(AdminSecureMixin, ModelView):
    """View base para todos os modelos com segurança."""
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 50


class UserAdmin(SecureModelView):
    column_list = ['id', 'name', 'email', 'is_active', 'created_at']
    column_searchable_list = ['name', 'email']
    column_filters = ['is_active', 'created_at']
    form_columns = ['name', 'email', 'password', 'is_active']
    column_labels = {
        'id': 'ID',
        'name': 'Nome',
        'email': 'E-mail',
        'is_active': 'Ativo',
        'created_at': 'Criado em',
    }


class ProductAdmin(SecureModelView):
    column_list = ['id', 'google_product_id', 'title',
                   'str_current_price', 'rating', 'created_at']
    column_searchable_list = ['title', 'google_product_id']
    column_filters = ['rating', 'created_at']
    column_labels = {
        'id': 'ID',
        'google_product_id': 'ID Google',
        'title': 'Título',
        'str_current_price': 'Preço (texto)',
        'rating': 'Avaliação',
        'created_at': 'Criado em',
    }


class OfferAdmin(SecureModelView):
    column_list = ['id', 'product.title', 'merchant',
                   'current_price', 'shipping_price', 'rating']
    column_searchable_list = ['merchant']
    column_filters = ['rating', 'current_price']
    column_labels = {
        'id': 'ID',
        'product.title': 'Produto',
        'merchant': 'Loja',
        'current_price': 'Preço',
        'shipping_price': 'Frete',
        'rating': 'Avaliação',
    }


class PriceHistoryAdmin(SecureModelView):
    column_list = ['id', 'offer.merchant',
                   'offer.product.title', 'price', 'captured_at']
    column_filters = ['captured_at']
    column_default_sort = ('captured_at', True)
    column_labels = {
        'id': 'ID',
        'offer.merchant': 'Loja',
        'offer.product.title': 'Produto',
        'price': 'Preço',
        'captured_at': 'Capturado em',
    }
    can_create = False
    can_edit = False
    can_delete = False


class ProductMonitoringAdmin(SecureModelView):
    column_list = ['id', 'user.email', 'product.title',
                   'desired_price', 'is_active', 'created_at']
    column_filters = ['is_active', 'created_at']
    column_searchable_list = ['user.email', 'product.title']
    column_labels = {
        'id': 'ID',
        'user.email': 'Usuário',
        'product.title': 'Produto',
        'desired_price': 'Preço Alvo',
        'is_active': 'Ativo',
        'created_at': 'Criado em',
    }


class NotificationAdmin(SecureModelView):
    column_list = ['id', 'user.email', 'product.title',
                   'title', 'message', 'sent_at']
    column_filters = ['sent_at']
    column_default_sort = ('sent_at', True)
    column_labels = {
        'id': 'ID',
        'user.email': 'Usuário',
        'product.title': 'Produto',
        'title': 'Título',
        'message': 'Mensagem',
        'sent_at': 'Enviado em',
    }
    can_create = False
    can_edit = False


def init_admin(app):
    """Inicializa o Flask-Admin com proteção por login."""
    admin = Admin(
        app,
        name='PriceAlert Admin',
        index_view=AdminHomeView(
            name='Dashboard',
            template='admin/index.html',
            url='/admin'
        ),
    )

    # Registra os modelos
    admin.add_view(UserAdmin(User, db.session, name='Usuários'))
    admin.add_view(ProductAdmin(Product, db.session, name='Produtos'))
    admin.add_view(OfferAdmin(Offer, db.session, name='Ofertas'))
    admin.add_view(PriceHistoryAdmin(
        PriceHistory, db.session, name='Histórico de Preços'))
    admin.add_view(ProductMonitoringAdmin(
        ProductMonitoring, db.session, name='Monitoramentos'))
    admin.add_view(NotificationAdmin(
        Notification, db.session, name='Notificações'))

    app.logger.info("Flask-Admin inicializado em /admin")
