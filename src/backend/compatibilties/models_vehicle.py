from sqlalchemy import Column, String
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