from pydantic import BaseModel


class GenerateVehicleDictionaryRequest(BaseModel):
    user_id: str


class GenerateVehicleDictionaryResponse(BaseModel):
    job_id: str
    message: str