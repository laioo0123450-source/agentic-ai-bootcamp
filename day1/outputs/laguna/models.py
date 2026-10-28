from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

class AssetBase(BaseModel):
    asset_id: str
    asset_type: str
    unit: str
    location: str
    install_year: int
    last_inspection: Optional[str] = None
    operating_hours: float
    status: str
    criticality: str
    notes: Optional[str] = ""

    @field_validator('asset_id')
    @classmethod
    def validate_asset_id(cls, v):
        if not re.match(r'^[A-Z]{3}-\d{4}$', v):
            raise ValueError('asset_id must follow XXX-nnnn format (e.g., MOT-0001)')
        return v

    @field_validator('criticality')
    @classmethod
    def validate_criticality(cls, v):
        if v not in ['High', 'Medium', 'Low']:
            raise ValueError('criticality must be High, Medium, or Low')
        return v

class Asset(AssetBase):
    deleted: bool = False
    model_config = {"from_attributes": True}

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
    criticality: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('criticality')
    @classmethod
    def validate_criticality(cls, v):
        if v is not None and v not in ['High', 'Medium', 'Low']:
            raise ValueError('criticality must be High, Medium, or Low')
        return v
