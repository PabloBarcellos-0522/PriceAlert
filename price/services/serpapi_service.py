import serpapi
from flask import current_app


class SerpApiService:

    def __init__(self, serpapi_api_key: str):
        self.client = serpapi.Client(api_key=serpapi_api_key)

    def search(self, query):
        results = self.client.search({
            "engine": "google_shopping_light",
            "q": query,
            "google_domain": "google.com.br",
            "gl": "br",
            "hl": "pt-BR"
        })
        return results

    def get_product_details(self, page_token, next_page_token=None):
        results = self.client.search({
            "engine": "google_immersive_product",
            "page_token": page_token,
            "google_domain": "google.com.br",
            "gl": "br",
            "hl": "pt-BR",
            "next_page_token": next_page_token
        })
        return results
