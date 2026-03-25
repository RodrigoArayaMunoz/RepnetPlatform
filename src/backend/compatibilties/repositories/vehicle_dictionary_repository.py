from typing import Iterable, Optional
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

    def _bulk_upsert(self, model, rows: Iterable[dict]) -> int:
        rows = list(rows)
        if not rows:
            return 0

        stmt = insert(model).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={"name": stmt.excluded.name},
        )
        self.db.execute(stmt)
        self.db.commit()
        return len(rows)

    def save_brands(self, rows: list[dict]) -> int:
        return self._bulk_upsert(VehicleBrand, rows)

    def save_models(self, rows: list[dict]) -> int:
        return self._bulk_upsert(VehicleModel, rows)

    def save_years(self, rows: list[dict]) -> int:
        return self._bulk_upsert(VehicleYear, rows)

    def save_versions(self, rows: list[dict]) -> int:
        return self._bulk_upsert(VehicleVersion, rows)

    def save_engines(self, rows: list[dict]) -> int:
        return self._bulk_upsert(VehicleEngine, rows)

    def save_transmissions(self, rows: list[dict]) -> int:
        return self._bulk_upsert(VehicleTransmission, rows)

    def _find_by_name(self, model, name: str) -> Optional[str]:
        row = self.db.query(model).filter(model.name.ilike(name.strip())).first()
        return row.id if row else None

    def get_brand_id_by_name(self, name: str) -> Optional[str]:
        return self._find_by_name(VehicleBrand, name)

    def get_model_id_by_name(self, name: str) -> Optional[str]:
        return self._find_by_name(VehicleModel, name)

    def get_year_id_by_name(self, name: str) -> Optional[str]:
        return self._find_by_name(VehicleYear, name)

    def get_version_id_by_name(self, name: str) -> Optional[str]:
        return self._find_by_name(VehicleVersion, name)

    def get_engine_id_by_name(self, name: str) -> Optional[str]:
        return self._find_by_name(VehicleEngine, name)

    def get_transmission_id_by_name(self, name: str) -> Optional[str]:
        return self._find_by_name(VehicleTransmission, name)