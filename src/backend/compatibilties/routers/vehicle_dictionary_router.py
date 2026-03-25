from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult

from celery_app import celery_app
from schemas_vehicle import SyncDictionaryResponse
from tasks.vehicle_dictionary_tasks import (
    sync_vehicle_dictionary_task,
    generate_vehicle_dictionary_task,
)

router = APIRouter(tags=["Vehicle Dictionary"])


class GenerateVehicleDictionaryRequest(BaseModel):
    user_id: str


class GenerateVehicleDictionaryResponse(BaseModel):
    job_id: str
    message: str


@router.post("/vehicle-dictionary/sync", response_model=SyncDictionaryResponse)
def sync_vehicle_dictionary():
    task = sync_vehicle_dictionary_task.delay()
    return SyncDictionaryResponse(
        message="Sincronización del diccionario iniciada",
        task_id=task.id,
    )


@router.post(
    "/vehicle-dictionary/generate",
    response_model=GenerateVehicleDictionaryResponse,
)
def generate_vehicle_dictionary(payload: GenerateVehicleDictionaryRequest):
    """
    Endpoint que usa tu frontend en LoadVehicleDictionary.jsx.
    Dispara la tarea Celery y devuelve el task_id como job_id.
    """
    task = generate_vehicle_dictionary_task.delay(payload.user_id)

    return GenerateVehicleDictionaryResponse(
        job_id=task.id,
        message="Generación del diccionario vehicular iniciada",
    )


@router.get("/imports/{job_id}")
def get_import_status(job_id: str):
    """
    Endpoint para polling de estado.
    Tu frontend espera:
    {
      status: "processing" | "success" | "error",
      progress: number,
      message: string
    }
    """
    task_result = AsyncResult(job_id, app=celery_app)

    if task_result.state == "PENDING":
        return {
            "status": "processing",
            "progress": 0,
            "message": "Proceso en cola...",
        }

    if task_result.state == "PROGRESS":
        meta = task_result.info or {}
        return {
            "status": "processing",
            "progress": meta.get("progress", 0),
            "message": meta.get("message", "Procesando..."),
        }

    if task_result.state == "SUCCESS":
        result_data = task_result.result or {}
        return {
            "status": "success",
            "progress": 100,
            "message": result_data.get(
                "message",
                "Diccionario vehicular generado correctamente",
            ),
        }

    if task_result.state in ["FAILURE", "REVOKED"]:
        error_message = str(task_result.info) if task_result.info else "Error en el proceso"
        return {
            "status": "error",
            "progress": 0,
            "message": error_message,
        }

    return {
        "status": "processing",
        "progress": 0,
        "message": f"Estado actual: {task_result.state}",
    }


@router.get("/imports/{job_id}/result")
def get_import_result(job_id: str):
    """
    Endpoint que consume tu ResultModal.
    Debe devolver:
    {
      summary: {...},
      results: {...}
    }
    """
    task_result = AsyncResult(job_id, app=celery_app)

    if task_result.state != "SUCCESS":
        raise HTTPException(
            status_code=400,
            detail="El proceso aún no ha finalizado correctamente.",
        )

    result_data = task_result.result or {}

    return {
        "summary": result_data.get("summary", {}),
        "results": result_data.get("results", {}),
    }