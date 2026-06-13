from decimal import Decimal
from datetime import datetime
from price.ext.db import db
from price.models.product_monitoring import ProductMonitoring
from price.models.notification import Notification
from price.models.price_history import PriceHistory
from price.models.offer import Offer
from price.models.product import Product


def get_index_data(user_id):
    """
    Retorna os alertas (notificações) e histórico de preços do usuário logado.
    """
    alertas = []
    historico = []

    # 1) Alertas (Notificações)
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

    # 2) Histórico de Preços
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

    return alertas, historico


def get_dashboard_data(user_id):
    """
    Retorna as estatísticas agregadas e informações para o dashboard do usuário.
    """
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

    return {
        "total_monitorados": total_monitorados,
        "total_alertas": total_alertas,
        "economia_total": economia_total,
        "total_lojas": total_lojas,
        "ultimas_quedas": ultimas_quedas,
        "monitoramentos_recentes": monitorings[:5]
    }
