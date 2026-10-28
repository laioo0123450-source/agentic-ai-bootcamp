from datetime import date
from enum import Enum
import re
from pydantic import BaseModel, field_validator

class Criticality(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

ASSET_ID_PATTERN = re.compile(r"^[A-Z]{3}-\d{4}$")

class AssetBase(BaseModel):
    asset_id: str
    asset_type: str
    unit: str
    location: str
    install_year: int
    last_inspection: date
    operating_hours: float
    status: str
    criticality: Criticality
    notes: str | None = None

    @field_validator("asset_id")
    @classmethod
    def validate_asset_id(cls, v: str) -> str:
        if not ASSET_ID_PATTERN.match(v):
            raise ValueError("asset_id must match ^[A-Z]{3}-\\d{4}$")
        return v

    @field_validator("criticality")
    @classmethod
    def validate_criticality(cls, v: Criticality) -> Criticality:
        if v not in Criticality:
            raise ValueError("criticality must be High, Medium, or Low")
        return v

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    asset_type: str | None = None
    unit: str | None = None
    location: str | None = None
    install_year: int | None = None
    last_inspection: date | None = None
    operating_hours: float | None = None
    status: str | None = None
    criticality: Criticality | None = None
    notes: str | None = None

    @field_validator("criticality")
    @classmethod
    def validate_criticality(cls, v: Criticality | None) -> Criticality | None:
        if v is not None and v not in Criticality:
            raise ValueError("criticality must be High, Medium, or Low")
        return v

class AssetResponse(AssetBase):
    model_config = {"from_attributes": True}

class FlaggedAssetResponse(AssetResponse):
    pass