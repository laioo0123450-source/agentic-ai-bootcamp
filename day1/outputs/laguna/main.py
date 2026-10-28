from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import pandas as pd
from fastapi import Request
import re

app = FastAPI()

# In-memory storage
assets_db = []

# Load CSV data on startup
@app.on_event("startup")
def load_data():
    global assets_db
    df = pd.read_csv("maintenance_assets.csv")
    for _, row in df.iterrows():
        asset = {
            "asset_id": str(row["asset_id"]),
            "asset_type": str(row["asset_type"]),
            "unit": str(row["unit"]),
            "location": str(row["location"]),
            "install_year": int(row["install_year"]),
            "last_inspection": str(row["last_inspection"]) if pd.notna(row["last_inspection"]) else None,
            "operating_hours": float(row["operating_hours"]) if pd.notna(row["operating_hours"]) else 0,
            "status": str(row["status"]),
            "criticality": str(row["criticality"]),
            "notes": str(row["notes"]) if pd.notna(row["notes"]) else "",
            "deleted": False
        }
        assets_db.append(asset)

# Pydantic Models
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

# Endpoints
@app.post("/assets", response_model=Asset)
def create_asset(asset: AssetCreate):
    for db_asset in assets_db:
        if db_asset["asset_id"] == asset.asset_id and not db_asset.get("deleted", False):
            raise HTTPException(status_code=400, detail=f"Asset with ID {asset.asset_id} already exists")
    asset_dict = asset.model_dump()
    asset_dict["deleted"] = False
    assets_db.append(asset_dict)
    return asset_dict

@app.get("/assets", response_model=List[Asset])
def list_assets(
    status: Optional[str] = None,
    unit: Optional[str] = None,
    criticality: Optional[str] = None
):
    result = [a for a in assets_db if not a.get("deleted", False)]
    if status:
        result = [a for a in result if a["status"] == status]
    if unit:
        result = [a for a in result if a["unit"] == unit]
    if criticality:
        result = [a for a in result if a["criticality"] == criticality]
    return result

@app.get("/assets/{asset_id}", response_model=Asset)
def get_asset(asset_id: str):
    for asset in assets_db:
        if asset["asset_id"] == asset_id and not asset.get("deleted", False):
            return asset
    raise HTTPException(status_code=404, detail="Asset not found")


@app.put("/assets/{asset_id}", response_model=Asset)
async def update_asset(asset_id: str, request: Request):
    data = await request.json()

    if "asset_id" in data:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify asset_id"
        )

    try:
        asset_update = AssetUpdate.model_validate(data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=exc.errors(include_context=False)
        ) from exc

    for idx, db_asset in enumerate(assets_db):
        if db_asset["asset_id"] == asset_id and not db_asset.get("deleted", False):
            if asset_update.asset_type is not None:
                assets_db[idx]["asset_type"] = asset_update.asset_type

            if asset_update.unit is not None:
                assets_db[idx]["unit"] = asset_update.unit

            if asset_update.location is not None:
                assets_db[idx]["location"] = asset_update.location

            if asset_update.install_year is not None:
                assets_db[idx]["install_year"] = asset_update.install_year

            if asset_update.last_inspection is not None:
                assets_db[idx]["last_inspection"] = asset_update.last_inspection

            if asset_update.operating_hours is not None:
                assets_db[idx]["operating_hours"] = asset_update.operating_hours

            if asset_update.status is not None:
                assets_db[idx]["status"] = asset_update.status

            if asset_update.criticality is not None:
                assets_db[idx]["criticality"] = asset_update.criticality

            if asset_update.notes is not None:
                assets_db[idx]["notes"] = asset_update.notes

            return assets_db[idx]

    raise HTTPException(
        status_code=404,
        detail="Asset not found"
    )


@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: str):
    for idx, db_asset in enumerate(assets_db):
        if db_asset["asset_id"] == asset_id and not db_asset.get("deleted", False):
            assets_db[idx]["deleted"] = True
            return {"message": f"Asset {asset_id} was successfully deleted (soft delete)"}
    raise HTTPException(status_code=404, detail="Asset not found")

# Custom exception handler for validation errors
@app.exception_handler(ValueError)
async def value_error_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {
                    "loc": ["body"],
                    "msg": str(exc),
                    "type": "value_error"
                }
            ]
        },
    )
