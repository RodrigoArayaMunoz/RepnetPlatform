import pandas as pd

from constants import (
    SEARCH_STATUS_ERROR,
)
from repositories.vehicle_dictionary_repository import VehicleDictionaryRepository
from services.mercadolibre_vehicle_service import MercadoLibreVehicleService


class ExcelCompatibilityService:
    REQUIRED_COLUMNS = [
        "MARCA",
        "MODELO",
        "AÑO",
        "VERSION",
        "MOTOR",
        "TRANSMISION",
    ]

    def __init__(self, dictionary_repo: VehicleDictionaryRepository):
        self.dictionary_repo = dictionary_repo
        self.meli_service = MercadoLibreVehicleService()

    def read_excel(self, file_path: str):
        df = pd.read_excel(file_path)
        missing = [c for c in self.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Faltan columnas obligatorias: {', '.join(missing)}")
        return df

    def process_row(self, row: dict, item_id: str, row_number: int) -> dict:
        brand_name = str(row.get("MARCA", "")).strip()
        model_name = str(row.get("MODELO", "")).strip()
        year_name = str(row.get("AÑO", "")).strip()
        version_name = str(row.get("VERSION", "")).strip()
        engine_name = str(row.get("MOTOR", "")).strip()
        transmission_name = str(row.get("TRANSMISION", "")).strip()

        brand_id = self.dictionary_repo.get_brand_id_by_name(brand_name)
        model_id = self.dictionary_repo.get_model_id_by_name(model_name)
        year_id = self.dictionary_repo.get_year_id_by_name(year_name)
        version_id = self.dictionary_repo.get_version_id_by_name(version_name)
        engine_id = self.dictionary_repo.get_engine_id_by_name(engine_name)
        transmission_id = self.dictionary_repo.get_transmission_id_by_name(transmission_name)

        base = {
            "row_number": row_number,
            "item_id": item_id,
            "brand_name": brand_name,
            "brand_id": brand_id,
            "model_name": model_name,
            "model_id": model_id,
            "year_name": year_name,
            "year_id": year_id,
            "version_name": version_name,
            "version_id": version_id,
            "engine_name": engine_name,
            "engine_id": engine_id,
            "transmission_name": transmission_name,
            "transmission_id": transmission_id,
        }

        if not all([brand_id, model_id, year_id, version_id, engine_id]):
            base["search_status"] = SEARCH_STATUS_ERROR
            base["error_message"] = "No se pudieron resolver todos los IDs desde tablas locales"
            base["product_id"] = None
            base["search_payload"] = {}
            base["search_response"] = {}
            return base

        resolution = self.meli_service.resolve_product_id(
            brand_id=brand_id,
            model_id=model_id,
            year_id=year_id,
            version_id=version_id,
            engine_id=engine_id,
            transmission_id=transmission_id,
        )

        base["search_status"] = resolution["status"]
        base["product_id"] = resolution["product_id"]
        base["search_payload"] = resolution["payload"]
        base["search_response"] = resolution["response"]
        base["error_message"] = None if resolution["status"] == "RESOLVED" else resolution["status"]

        return base