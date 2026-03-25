from celery.utils.log import get_task_logger
from db import SessionLocal

from celery_app import celery_app
from repositories.vehicle_dictionary_repository import VehicleDictionaryRepository
from services.mercadolibre_vehicle_service import MercadoLibreVehicleService

logger = get_task_logger(__name__)


def _safe_percent(current: int, total: int, start: int = 0, end: int = 100) -> int:
    if total <= 0:
        return start
    ratio = current / total
    value = start + int((end - start) * ratio)
    return max(start, min(end, value))


@celery_app.task(bind=True, name="sync_vehicle_dictionary_task")
def sync_vehicle_dictionary_task(self):
    db = SessionLocal()
    try:
        self.update_state(
            state="PROGRESS",
            meta={
                "progress": 5,
                "message": "Iniciando sincronización del diccionario vehicular...",
            },
        )

        repo = VehicleDictionaryRepository(db)
        service = MercadoLibreVehicleService()

        brands_map = {}
        models_map = {}
        years_map = {}
        versions_map = {}
        engines_map = {}
        transmissions_map = {}

        self.update_state(
            state="PROGRESS",
            meta={
                "progress": 10,
                "message": "Consultando marcas en Mercado Libre...",
            },
        )

        brands = service.fetch_brands()
        total_brands = len(brands)

        if total_brands == 0:
            self.update_state(
                state="PROGRESS",
                meta={
                    "progress": 100,
                    "message": "No se encontraron marcas para sincronizar.",
                },
            )
            return {
                "message": "No se encontraron datos para generar el diccionario",
                "summary": {
                    "brands": 0,
                    "models": 0,
                    "years": 0,
                    "versions": 0,
                    "engines": 0,
                    "transmissions": 0,
                },
                "results": {
                    "brands_saved": 0,
                    "models_saved": 0,
                    "years_saved": 0,
                    "versions_saved": 0,
                    "engines_saved": 0,
                    "transmissions_saved": 0,
                },
            }

        for index, brand in enumerate(brands, start=1):
            brands_map[brand["id"]] = brand

            progress = _safe_percent(index, total_brands, start=15, end=85)
            brand_name = brand.get("name", brand.get("id", "N/A"))

            self.update_state(
                state="PROGRESS",
                meta={
                    "progress": progress,
                    "message": f"Procesando marca {index}/{total_brands}: {brand_name}",
                },
            )

            models = service.fetch_models(brand["id"])
            for model in models:
                models_map[model["id"]] = model

                years = service.fetch_years(brand["id"], model["id"])
                for year in years:
                    years_map[year["id"]] = year

                    versions = service.fetch_versions(
                        brand["id"],
                        model["id"],
                        year["id"],
                    )
                    for version in versions:
                        versions_map[version["id"]] = version

                        engines = service.fetch_engines(
                            brand["id"],
                            model["id"],
                            year["id"],
                            version["id"],
                        )
                        for engine in engines:
                            engines_map[engine["id"]] = engine

                            transmissions = service.fetch_transmissions(
                                brand["id"],
                                model["id"],
                                year["id"],
                                version["id"],
                                engine["id"],
                            )
                            for transmission in transmissions:
                                transmissions_map[transmission["id"]] = transmission

        self.update_state(
            state="PROGRESS",
            meta={
                "progress": 90,
                "message": "Guardando marcas, modelos, años, versiones, motores y transmisiones en la base de datos...",
            },
        )

        saved = {
            "brands": repo.save_brands(list(brands_map.values())),
            "models": repo.save_models(list(models_map.values())),
            "years": repo.save_years(list(years_map.values())),
            "versions": repo.save_versions(list(versions_map.values())),
            "engines": repo.save_engines(list(engines_map.values())),
            "transmissions": repo.save_transmissions(list(transmissions_map.values())),
        }

        self.update_state(
            state="PROGRESS",
            meta={
                "progress": 100,
                "message": "Diccionario vehicular generado correctamente.",
            },
        )

        summary = {
            "brands": len(brands_map),
            "models": len(models_map),
            "years": len(years_map),
            "versions": len(versions_map),
            "engines": len(engines_map),
            "transmissions": len(transmissions_map),
        }

        results = {
            "brands_saved": saved["brands"],
            "models_saved": saved["models"],
            "years_saved": saved["years"],
            "versions_saved": saved["versions"],
            "engines_saved": saved["engines"],
            "transmissions_saved": saved["transmissions"],
        }

        logger.info("Vehicle dictionary synced: %s", saved)

        return {
            "message": "Diccionario vehicular generado correctamente",
            "summary": summary,
            "results": results,
        }

    except Exception as exc:
        logger.exception("Error syncing vehicle dictionary")
        raise exc
    finally:
        db.close()


@celery_app.task(bind=True, name="generate_vehicle_dictionary_task")
def generate_vehicle_dictionary_task(self, user_id: str):
    """
    Esta task la dejo separada porque tu frontend actual llama:
    POST /vehicle-dictionary/generate
    y envía user_id.
    Por ahora reutiliza la misma lógica de sync_vehicle_dictionary_task.
    """
    db = SessionLocal()
    try:
        self.update_state(
            state="PROGRESS",
            meta={
                "progress": 5,
                "message": f"Iniciando generación del diccionario para el usuario {user_id}...",
            },
        )

        repo = VehicleDictionaryRepository(db)
        service = MercadoLibreVehicleService()

        brands_map = {}
        models_map = {}
        years_map = {}
        versions_map = {}
        engines_map = {}
        transmissions_map = {}

        self.update_state(
            state="PROGRESS",
            meta={
                "progress": 10,
                "message": "Consultando marcas en Mercado Libre...",
            },
        )

        brands = service.fetch_brands()
        total_brands = len(brands)

        if total_brands == 0:
            return {
                "message": "No se encontraron datos para generar el diccionario",
                "summary": {
                    "brands": 0,
                    "models": 0,
                    "years": 0,
                    "versions": 0,
                    "engines": 0,
                    "transmissions": 0,
                },
                "results": {
                    "brands_saved": 0,
                    "models_saved": 0,
                    "years_saved": 0,
                    "versions_saved": 0,
                    "engines_saved": 0,
                    "transmissions_saved": 0,
                    "user_id": user_id,
                },
            }

        for index, brand in enumerate(brands, start=1):
            brands_map[brand["id"]] = brand

            progress = _safe_percent(index, total_brands, start=15, end=85)
            brand_name = brand.get("name", brand.get("id", "N/A"))

            self.update_state(
                state="PROGRESS",
                meta={
                    "progress": progress,
                    "message": f"Procesando marca {index}/{total_brands}: {brand_name}",
                },
            )

            models = service.fetch_models(brand["id"])
            for model in models:
                models_map[model["id"]] = model

                years = service.fetch_years(brand["id"], model["id"])
                for year in years:
                    years_map[year["id"]] = year

                    versions = service.fetch_versions(
                        brand["id"],
                        model["id"],
                        year["id"],
                    )
                    for version in versions:
                        versions_map[version["id"]] = version

                        engines = service.fetch_engines(
                            brand["id"],
                            model["id"],
                            year["id"],
                            version["id"],
                        )
                        for engine in engines:
                            engines_map[engine["id"]] = engine

                            transmissions = service.fetch_transmissions(
                                brand["id"],
                                model["id"],
                                year["id"],
                                version["id"],
                                engine["id"],
                            )
                            for transmission in transmissions:
                                transmissions_map[transmission["id"]] = transmission

        self.update_state(
            state="PROGRESS",
            meta={
                "progress": 90,
                "message": "Guardando resultados en la base de datos...",
            },
        )

        saved = {
            "brands": repo.save_brands(list(brands_map.values())),
            "models": repo.save_models(list(models_map.values())),
            "years": repo.save_years(list(years_map.values())),
            "versions": repo.save_versions(list(versions_map.values())),
            "engines": repo.save_engines(list(engines_map.values())),
            "transmissions": repo.save_transmissions(list(transmissions_map.values())),
        }

        self.update_state(
            state="PROGRESS",
            meta={
                "progress": 100,
                "message": "Diccionario vehicular generado correctamente.",
            },
        )

        summary = {
            "brands": len(brands_map),
            "models": len(models_map),
            "years": len(years_map),
            "versions": len(versions_map),
            "engines": len(engines_map),
            "transmissions": len(transmissions_map),
        }

        results = {
            "brands_saved": saved["brands"],
            "models_saved": saved["models"],
            "years_saved": saved["years"],
            "versions_saved": saved["versions"],
            "engines_saved": saved["engines"],
            "transmissions_saved": saved["transmissions"],
            "user_id": user_id,
        }

        logger.info("Vehicle dictionary generated for user %s: %s", user_id, saved)

        return {
            "message": "Diccionario vehicular generado correctamente",
            "summary": summary,
            "results": results,
        }

    except Exception as exc:
        logger.exception("Error generating vehicle dictionary for user %s", user_id)
        raise exc
    finally:
        db.close()