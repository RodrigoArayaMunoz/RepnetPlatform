from celery.utils.log import get_task_logger
from db import SessionLocal

from celery_app import celery_app
from repositories.vehicle_dictionary_repository import VehicleDictionaryRepository
from services.mercadolibre_vehicle_service import MercadoLibreVehicleService

logger = get_task_logger(__name__)


@celery_app.task(name="sync_vehicle_dictionary_task")
def sync_vehicle_dictionary_task():
    db = SessionLocal()
    try:
        repo = VehicleDictionaryRepository(db)
        service = MercadoLibreVehicleService()

        brands_map = {}
        models_map = {}
        years_map = {}
        versions_map = {}
        engines_map = {}
        transmissions_map = {}

        brands = service.fetch_brands()
        for brand in brands:
            brands_map[brand["id"]] = brand

            models = service.fetch_models(brand["id"])
            for model in models:
                models_map[model["id"]] = model

                years = service.fetch_years(brand["id"], model["id"])
                for year in years:
                    years_map[year["id"]] = year

                    versions = service.fetch_versions(brand["id"], model["id"], year["id"])
                    for version in versions:
                        versions_map[version["id"]] = version

                        engines = service.fetch_engines(brand["id"], model["id"], year["id"], version["id"])
                        for engine in engines:
                            engines_map[engine["id"]] = engine

                            transmissions = service.fetch_transmissions(
                                brand["id"], model["id"], year["id"], version["id"], engine["id"]
                            )
                            for transmission in transmissions:
                                transmissions_map[transmission["id"]] = transmission

        saved = {
            "brands": repo.save_brands(list(brands_map.values())),
            "models": repo.save_models(list(models_map.values())),
            "years": repo.save_years(list(years_map.values())),
            "versions": repo.save_versions(list(versions_map.values())),
            "engines": repo.save_engines(list(engines_map.values())),
            "transmissions": repo.save_transmissions(list(transmissions_map.values())),
        }

        logger.info("Vehicle dictionary synced: %s", saved)
        return {"status": "success", "saved": saved}
    finally:
        db.close()