from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from models_vehicle import (
    VehicleBrand,
    VehicleModel,
    VehicleYear,
    VehicleVersion,
    VehicleEngine,
    VehicleTransmission,
)


class VehicleDictionaryRepository:
    def __init__(self, db: Session):
        self.db = db

    def _upsert(self, model, rows: list[dict]) -> int:
        """
        Upsert masivo sobre `id` (primary key).
        Si el registro ya existe, actualiza el nombre.
        """
        if not rows:
            return 0

        stmt = (
            insert(model)
            .values(rows)
            .on_conflict_do_update(
                index_elements=["id"],          # ← tu PK es `id`, no `ml_id`
                set_={"name": insert(model).excluded.name},
            )
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    # Los datos de ML ya vienen como {id, name} → encajan directo con el modelo
    def save_brands(self, items: list[dict]) -> int:
        return self._upsert(VehicleBrand, items)

    def save_models(self, items: list[dict]) -> int:
        return self._upsert(VehicleModel, items)

    def save_years(self, items: list[dict]) -> int:
        return self._upsert(VehicleYear, items)

    def save_versions(self, items: list[dict]) -> int:
        return self._upsert(VehicleVersion, items)

    def save_engines(self, items: list[dict]) -> int:
        return self._upsert(VehicleEngine, items)

    def save_transmissions(self, items: list[dict]) -> int:
        return self._upsert(VehicleTransmission, items)