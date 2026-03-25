import requests
from constants import ML_VEHICLE_DOMAIN_ID
from services.token_store import token_store
import logging
logger = logging.getLogger(__name__)

ATTR_BRAND        = "BRAND"
ATTR_MODEL        = "CAR_AND_VAN_MODEL"
ATTR_YEAR         = "YEAR"
ATTR_VERSION      = "CAR_AND_VAN_SUBMODEL"
ATTR_ENGINE       = "CAR_AND_VAN_ENGINE"
ATTR_TRANSMISSION = "TRANSMISSION_CONTROL_TYPE"


class MercadoLibreVehicleService:
    
    BASE_URL = "https://api.mercadolibre.com"


    def __init__(self, user_id: str):
        self.user_id = str(user_id)
        token_data = self._get_token_data_for_user(self.user_id)
        access_token = token_data.get("access_token")

        if not access_token:
            raise ValueError(f"No se encontró access_token para user_id={self.user_id}")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        })

    def _get_token_data_for_user(self, user_id: str) -> dict:
        token_data = token_store.get(user_id)
        if not token_data:
            raise ValueError(f"No existe token almacenado para user_id={user_id}")
        return token_data

    def _get_top_values(self, attribute_id: str) -> list[dict]:
        url = f"{self.base_url}/catalog_domains/{self.domain_id}/attributes/{attribute_id}/top_values"
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        raw_values = data if isinstance(data, list) else data.get("values", [])

        return [
            {"id": str(v["id"]), "name": str(v["name"]).strip()}
            for v in raw_values
            if v.get("id") and v.get("name")
        ]

    def fetch_brands(self) -> list[dict]:
        return self._get_top_values(ATTR_BRAND)

    def fetch_models(self) -> list[dict]:
        return self._get_top_values(ATTR_MODEL)

    def fetch_years(self) -> list[dict]:
        return self._get_top_values(ATTR_YEAR)

    def fetch_versions(self) -> list[dict]:
        return self._get_top_values(ATTR_VERSION)

    def fetch_engines(self) -> list[dict]:
        return self._get_top_values(ATTR_ENGINE)

    def fetch_transmissions(self) -> list[dict]:
        return self._get_top_values(ATTR_TRANSMISSION)