from sqlalchemy import Column, String, Integer, Text, DateTime, func
from db import Base


class VehicleBrand(Base):
    __tablename__ = "vehicle_brands"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)


class VehicleModel(Base):
    __tablename__ = "vehicle_models"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)


class VehicleYear(Base):
    __tablename__ = "vehicle_years"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)


class VehicleVersion(Base):
    __tablename__ = "vehicle_versions"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)


class VehicleEngine(Base):
    __tablename__ = "vehicle_engines"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)


class VehicleTransmission(Base):
    __tablename__ = "vehicle_transmissions"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)


class CompatibilityImportJob(Base):
    __tablename__ = "compatibility_import_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    file_name = Column(String, nullable=False)
    item_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="PENDING", index=True)
    total_rows = Column(Integer, nullable=False, default=0)
    processed_rows = Column(Integer, nullable=False, default=0)
    resolved_rows = Column(Integer, nullable=False, default=0)
    error_rows = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class CompatibilityCandidate(Base):
    __tablename__ = "compatibility_candidates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, nullable=False, index=True)
    row_number = Column(Integer, nullable=False)

    item_id = Column(String, nullable=False, index=True)

    brand_name = Column(String, nullable=True)
    brand_id = Column(String, nullable=True, index=True)

    model_name = Column(String, nullable=True)
    model_id = Column(String, nullable=True, index=True)

    year_name = Column(String, nullable=True)
    year_id = Column(String, nullable=True, index=True)

    version_name = Column(String, nullable=True)
    version_id = Column(String, nullable=True, index=True)

    engine_name = Column(String, nullable=True)
    engine_id = Column(String, nullable=True, index=True)

    transmission_name = Column(String, nullable=True)
    transmission_id = Column(String, nullable=True, index=True)

    product_id = Column(String, nullable=True, index=True)

    search_status = Column(String, nullable=False, index=True)
    publish_status = Column(String, nullable=False, default="NOT_SENT", index=True)

    error_message = Column(Text, nullable=True)
    search_payload = Column(Text, nullable=True)
    search_response = Column(Text, nullable=True)
    publish_response = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)