from fastapi import APIRouter
from schemas_vehicle import SyncDictionaryResponse
from tasks.vehicle_dictionary_tasks import sync_vehicle_dictionary_task

router = APIRouter(prefix="/vehicle-dictionary", tags=["Vehicle Dictionary"])


@router.post("/sync", response_model=SyncDictionaryResponse)
def sync_vehicle_dictionary():
    task = sync_vehicle_dictionary_task.delay()
    return SyncDictionaryResponse(
        message="Sincronización del diccionario iniciada",
        task_id=task.id,
    )