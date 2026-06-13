from datetime import datetime, UTC
from decimal import Decimal
from flask import current_app
from typing import Optional
from price.ext.db import db
from price.models.product import Product
from price.models.offer import Offer
from price.models.price_history import PriceHistory


class SerpapiProductService:

    def search(self, query: str, fetch_offers: bool = False, max_details: int = 0):
        """Busca produtos no Google Shopping e opcionalmente busca detalhes/offers.

        - fetch_offers: se True, chama `get_product_details` para até `max_details` produtos.
        """
        results = current_app.serpapi_service.search(query)

        shopping_results = results.get("shopping_results", [])
        if not shopping_results:
            return []

        api_product_ids = [res.get("product_id")
                           for res in shopping_results if res.get("product_id")]
        existing_products = Product.query.filter(
            Product.google_product_id.in_(api_product_ids)).all()
        existing_products_dict = {
            p.google_product_id: p for p in existing_products}

        products_to_return = []
        details_count = 0
        for result in shopping_results:
            prod_id = result.get("product_id")
            if not prod_id:
                continue

            product = existing_products_dict.get(prod_id)
            if not product:
                product = Product(
                    google_product_id=prod_id,
                    title=result.get("title"),
                    str_current_price=result.get("price"),
                    rating=result.get("rating"),
                    review_count=result.get("reviews"),
                    product_token=result.get(
                        "immersive_product_page_token", ""),
                    product_shoping_link=result.get("product_link", ""),
                    image=result.get("thumbnail", ""),
                )
                db.session.add(product)
                db.session.flush()
                existing_products_dict[prod_id] = product

            # Se pediu, buscar ofertas detalhadas (pode ser custoso em rate-limit)
            if fetch_offers and details_count < max_details:
                page_token = result.get(
                    "immersive_product_page_token") or product.product_token
                if page_token:
                    try:
                        self.get_product_details(page_token)
                    except Exception:
                        # não falhar toda a busca por causa de detalhe
                        pass
                    details_count += 1

            products_to_return.append(product)

        db.session.commit()
        return products_to_return

    def get_product_details(self, page_token: str, next_page_token: Optional[str] = None, commit: bool = True):
        """Busca detalhes de produto (inclui lojas/offers) e persiste Offers e PriceHistory.

        Retorna um dict com os dados do SerpAPI e a lista de offers processadas.
        """
        results = current_app.serpapi_service.get_product_details(
            page_token, next_page_token)

        product_info = results.get("product_results") or {}
        # product_info pode ser um dict ou uma lista dependendo da resposta
        if isinstance(product_info, list):
            product_info = product_info[0] if product_info else {}

        google_id = product_info.get("product_id") or product_info.get("id")
        product = None
        if google_id:
            product = Product.query.filter_by(
                google_product_id=google_id).first()

        # Tenta recuperar por token se não tiver google_id
        if not product:
            token = page_token
            product = Product.query.filter_by(product_token=token).first()

        # Se ainda não existir, cria um produto mínimo
        if not product:
            product = Product(
                google_product_id=google_id or f"unknown-{token}",
                title=product_info.get("title", ""),
                str_current_price=product_info.get("price"),
                rating=product_info.get("rating"),
                review_count=product_info.get("reviews"),
                product_token=page_token,
                product_shoping_link=product_info.get("product_link", ""),
                image=(product_info.get("thumbnails") or [None])[0] if product_info.get(
                    "thumbnails") else product_info.get("thumbnail", "")
            )
            db.session.add(product)
            db.session.flush()
        else:
            product.updated_at = datetime.now(UTC)

        processed_offers = []

        stores = product_info.get("stores") or product_info.get("stores", [])
        for store in stores:
            merchant = store.get("name") or store.get("merchant")
            product_url = store.get("link")
            price_val = None
            # tenta extrair preço numérico
            if store.get("extracted_total") is not None:
                price_val = store.get("extracted_total")
            elif store.get("extracted_price") is not None:
                price_val = store.get("extracted_price")
            elif store.get("extracted_price") is None and store.get("price"):
                try:
                    price_val = float(str(store.get("price")).replace(
                        "R$", "").replace(".", "").replace(",", "."))
                except Exception:
                    price_val = None

            if price_val is None:
                continue

            current_price = Decimal(str(price_val))

            offer = None
            if product.id:
                offer = Offer.query.filter_by(
                    product_id=product.id, merchant=merchant, product_url=product_url).first()

            if not offer:
                offer = Offer(
                    product=product,
                    merchant=merchant or "",
                    product_url=product_url or "",
                    affiliate_url=store.get("affiliate_link"),
                    current_price=current_price,
                    shipping_price=Decimal(str(store.get("shipping"))) if store.get(
                        "shipping") else None,
                    rating=store.get("rating"),
                    reviews_count=store.get("reviews")
                )
                db.session.add(offer)
                db.session.flush()
            else:
                # Se preço mudou, registra histórico
                if offer.current_price != current_price:
                    ph = PriceHistory(offer=offer, price=offer.current_price)
                    db.session.add(ph)
                    offer.current_price = current_price

            processed_offers.append(offer)

        if commit:
            db.session.commit()

        return {"product": product, "offers": processed_offers, "raw": results}
