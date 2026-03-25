import requests

from constants import (
    ML_SITE_ID,
    ML_VEHICLE_DOMAIN_ID,
    ATTR_BRAND,
    ATTR_MODEL,
    ATTR_YEAR,
    ATTR_VERSION,
    ATTR_ENGINE,
    ATTR_TRANSMISSION,
)
from config import settings


class MercadoLibreVehicleService:
    BASE_URL = "https://api.mercadolibre.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                #"Authorization": f"Bearer {settings.ML_ACCESS_TOKEN}",
                "Authorization": f"Bearer {settings.ml_token_url}",
                "Content-Type": "application/json",
            }
        )

    def _post(self, path: str, payload: dict):
        resp = self.session.post(f"{self.BASE_URL}{path}", json=payload, timeout=90)
        resp.raise_for_status()
        return resp.json()

    def _normalize_option(self, value: dict) -> dict | None:
        value_id = value.get("id") or value.get("value_id")
        value_name = value.get("name") or value.get("value_name")
        if not value_id or not value_name:
            return None
        return {"id": str(value_id), "name": str(value_name).strip()}

    def _extract_attribute_values(self, response: dict, attribute_id: str) -> list[dict]:
        found = {}
        for result in response.get("results", []):
            for attr in result.get("attributes", []):
                if attr.get("id") != attribute_id:
                    continue

                for v in attr.get("values", []):
                    opt = self._normalize_option(v)
                    if opt:
                        found[opt["id"]] = opt

                opt = self._normalize_option(attr)
                if opt:
                    found[opt["id"]] = opt

        return list(found.values())

    def products_search_chunks(self, known_attributes: list[dict], limit: int = 50, offset: int = 0):
        payload = {
            "domain_id": ML_VEHICLE_DOMAIN_ID,
            "site_id": ML_SITE_ID,
            "known_attributes": known_attributes,
            "limit": limit,
            "offset": offset,
        }
        return self._post("/catalog_compatibilities/products_search/chunks", payload)

    def fetch_brands(self):
        data = self.products_search_chunks([])
        return self._extract_attribute_values(data, ATTR_BRAND)

    def fetch_models(self, brand_id: str):
        data = self.products_search_chunks([
            {"id": ATTR_BRAND, "value_ids": [brand_id]}
        ])
        return self._extract_attribute_values(data, ATTR_MODEL)

    def fetch_years(self, brand_id: str, model_id: str):
        data = self.products_search_chunks([
            {"id": ATTR_BRAND, "value_ids": [brand_id]},
            {"id": ATTR_MODEL, "value_ids": [model_id]},
        ])
        return self._extract_attribute_values(data, ATTR_YEAR)

    def fetch_versions(self, brand_id: str, model_id: str, year_id: str):
        data = self.products_search_chunks([
            {"id": ATTR_BRAND, "value_ids": [brand_id]},
            {"id": ATTR_MODEL, "value_ids": [model_id]},
            {"id": ATTR_YEAR, "value_ids": [year_id]},
        ])
        return self._extract_attribute_values(data, ATTR_VERSION)

    def fetch_engines(self, brand_id: str, model_id: str, year_id: str, version_id: str):
        data = self.products_search_chunks([
            {"id": ATTR_BRAND, "value_ids": [brand_id]},
            {"id": ATTR_MODEL, "value_ids": [model_id]},
            {"id": ATTR_YEAR, "value_ids": [year_id]},
            {"id": ATTR_VERSION, "value_ids": [version_id]},
        ])
        return self._extract_attribute_values(data, ATTR_ENGINE)

    def fetch_transmissions(self, brand_id: str, model_id: str, year_id: str, version_id: str, engine_id: str):
        data = self.products_search_chunks([
            {"id": ATTR_BRAND, "value_ids": [brand_id]},
            {"id": ATTR_MODEL, "value_ids": [model_id]},
            {"id": ATTR_YEAR, "value_ids": [year_id]},
            {"id": ATTR_VERSION, "value_ids": [version_id]},
            {"id": ATTR_ENGINE, "value_ids": [engine_id]},
        ])
        return self._extract_attribute_values(data, ATTR_TRANSMISSION)

    def resolve_product_id(
        self,
        *,
        brand_id: str,
        model_id: str,
        year_id: str,
        version_id: str,
        engine_id: str,
        transmission_id: str | None = None,
    ):
        known_attributes = [
            {"id": ATTR_BRAND, "value_ids": [brand_id]},
            {"id": ATTR_MODEL, "value_ids": [model_id]},
            {"id": ATTR_YEAR, "value_ids": [year_id]},
            {"id": ATTR_VERSION, "value_ids": [version_id]},
            {"id": ATTR_ENGINE, "value_ids": [engine_id]},
        ]

        if transmission_id:
            known_attributes.append(
                {"id": ATTR_TRANSMISSION, "value_ids": [transmission_id]}
            )

        response = self.products_search_chunks(known_attributes, limit=10, offset=0)
        results = response.get("results", [])

        if len(results) == 0:
            return {
                "status": "NOT_FOUND",
                "product_id": None,
                "payload": {"known_attributes": known_attributes},
                "response": response,
            }

        if len(results) > 1:
            return {
                "status": "AMBIGUOUS",
                "product_id": None,
                "payload": {"known_attributes": known_attributes},
                "response": response,
            }

        return {
            "status": "RESOLVED",
            "product_id": results[0].get("id"),
            "payload": {"known_attributes": known_attributes},
            "response": response,
        }

    def add_compatibility(self, item_id: str, product_id: str):
        payload = {
            "creation_source": "AUTOMATION",
            "products": [{"id": product_id}],
        }
        return self._post(f"/items/{item_id}/compatibilities", payload)