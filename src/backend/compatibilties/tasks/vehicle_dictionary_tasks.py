from celery.utils.log import get_task_logger
from db import SessionLocal
from celery_app import celery_app
from repositories.vehicle_dictionary_repository import VehicleDictionaryRepository
from services.mercadolibre_vehicle_service import MercadoLibreVehicleService

logger = get_task_logger(__name__)

# Orden, etiqueta legible, método del servicio, método del repo
SYNC_STEPS = [
    (10, "Marcas",         "fetch_brands",         "save_brands"),
    (25, "Modelos",        "fetch_models",         "save_models"),
    (40, "Años",           "fetch_years",           "save_years"),
    (55, "Versiones",      "fetch_versions",        "save_versions"),
    (70, "Motores",        "fetch_engines",         "save_engines"),
    (85, "Transmisiones",  "fetch_transmissions",   "save_transmissions"),
]


def _run_dictionary_sync(task, user_id: str):
    db = SessionLocal()
    try:
        task.update_state(state="PROGRESS", meta={
            "progress": 5,
            "message": "Iniciando sincronización del diccionario vehicular...",
        })

        svc  = MercadoLibreVehicleService(user_id=user_id)
        repo = VehicleDictionaryRepository(db)

        summary = {}

        for progress, label, fetch_method, save_method in SYNC_STEPS:

            task.update_state(state="PROGRESS", meta={
                "progress": progress,
                "message": f"Consultando {label} en MercadoLibre...",
            })

            items = getattr(svc, fetch_method)()
            saved = getattr(repo, save_method)(items)

            summary[label.lower()] = {"fetched": len(items), "saved": saved}
            logger.info(f"[VehicleSync] {label}: {len(items)} obtenidos, {saved} guardados.")

        task.update_state(state="PROGRESS", meta={
            "progress": 100,
            "message": "Diccionario vehicular sincronizado correctamente.",
        })

        return {
            "message": "Diccionario vehicular sincronizado correctamente",
            "user_id": user_id,
            "summary": summary,
        }

    except Exception as exc:
        logger.exception("Error sincronizando diccionario vehicular para user_id=%s", user_id)
        raise exc
    finally:
        db.close()


@celery_app.task(bind=True, name="generate_vehicle_dictionary_task")
def generate_vehicle_dictionary_task(self, user_id: str):
    return _run_dictionary_sync(self, str(user_id))