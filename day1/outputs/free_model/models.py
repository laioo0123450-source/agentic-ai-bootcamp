# models.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Literal
from datetime import date
import re


class AssetBase(BaseModel):
    asset_type: str
    unit: str
    location: str
    install_year: int = Field(..., ge=1900, le=2100)
    last_inspection: date
    operating_hours: float = Field(..., ge=0)
    status: str
    criticality: Literal["High", "Medium", "Low"]
    notes: Optional[str] = None

class AssetCreate(AssetBase):
    asset_id: str = Field(..., pattern=r'^[A-Z]{3}-\d{4}$')

class AssetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asset_type: Optional[str] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    install_year: Optional[int] = Field(None, ge=1900, le=2100)
    last_inspection: Optional[date] = None
    operating_hours: Optional[float] = Field(None, ge=0)
    status: Optional[str] = None
    criticality: Optional[Literal["High", "Medium", "Low"]] = None
    notes: Optional[str] = None

class Asset(AssetBase):
    asset_id: str
    deleted: bool = False

    @field_validator('asset_id')
    def validate_asset_id(cls, v):
        if not re.fullmatch(r'[A-Z]{3}-\d{4}', v):
            raise ValueError('asset_id must follow XXX-nnnn format')
        return v
