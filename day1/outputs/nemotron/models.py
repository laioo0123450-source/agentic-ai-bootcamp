# models.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class Criticality(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class AssetBase(BaseModel):
    asset_id: str = Field(..., pattern=r'^[A-Za-z]{3}-\d{4}$')
    asset_type: str
    unit: str
    location: str
    install_year: int
    last_inspection: str
    operating_hours: float
    status: str
    criticality: Criticality
    notes: Optional[str] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    asset_type: Optional[str] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    install_year: Optional[int] = None
    last_inspection: Optional[str] = None
    operating_hours: Optional[float] = None
    status: Optional[str] = None
    criticality: Optional[Criticality] = None
    notes: Optional[str] = None

class Asset(AssetBase):
    deleted: bool = False

    class Config:
        from_attributes = True
