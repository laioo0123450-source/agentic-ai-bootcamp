
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import List, Optional
import csv
from models import Asset, AssetCreate, AssetUpdate
from datetime import datetime
from fastapi.exceptions import RequestValidationError
from fastapi import Request
app = FastAPI(title="Asset Management API")

# In-memory storage
assets_db = {}

# Load CSV data
def load_assets():
    with open('maintenance_assets.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            asset = Asset(
                asset_id=row['asset_id'],
                asset_type=row['asset_type'],
                unit=row['unit'],
                location=row['location'],
                install_year=int(row['install_year']),
                                last_inspection=datetime.strptime(
                    row['last_inspection'], "%m/%d/%Y"
                ).date(),
                operating_hours=float(row['operating_hours']),
                status=row['status'],
                criticality=row['criticality'],
                notes=row.get('notes')
            )
            assets_db[asset.asset_id] = asset

load_assets()

# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = []
    for error in exc.errors():
        field = error['loc'][-1] if error['loc'] else 'unknown'
        errors.append({
            "field": field,
            "reason": error['msg']
        })
    return JSONResponse(
        status_code=422,
        content={"errors": errors}
    )

# Helper function to find asset
def get_asset(asset_id: str):
    asset = assets_db.get(asset_id)
    if not asset or asset.deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@app.post("/assets", response_model=Asset)
async def create_asset(asset: AssetCreate):
    if asset.asset_id in assets_db:
        raise HTTPException(status_code=400, detail="Asset ID already exists")
    new_asset = Asset(**asset.dict())
    assets_db[asset.asset_id] = new_asset
    return new_asset

@app.get("/assets", response_model=List[Asset])
async def list_assets(
    status: Optional[str] = Query(None),
    unit: Optional[str] = Query(None),
    criticality: Optional[str] = Query(None)
):
    filtered_assets = []
    for asset in assets_db.values():
        if asset.deleted:
            continue
        if status and asset.status != status:
            continue
        if unit and asset.unit != unit:
            continue
        if criticality and asset.criticality != criticality:
            continue
        filtered_assets.append(asset)
    return filtered_assets

@app.get("/assets/{asset_id}", response_model=Asset)
async def retrieve_asset(asset_id: str):
    return get_asset(asset_id)

@app.put("/assets/{asset_id}", response_model=Asset)
async def update_asset(asset_id: str, request: Request):
    asset = get_asset(asset_id)
    data = await request.json()

    if "asset_id" in data:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify asset_id"
        )

    asset_update = AssetUpdate(**data)
    update_data = asset_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(asset, key, value)

    return asset

@app.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str, soft_delete: bool = True):
    asset = get_asset(asset_id)
    if soft_delete:
        asset.deleted = True
        return {"message": "Asset soft deleted"}
    else:
        del assets_db[asset_id]
        return {"message": "Asset permanently deleted"}
