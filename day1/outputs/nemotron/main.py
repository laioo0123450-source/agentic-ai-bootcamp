# main.py
import os
import csv
import random
from datetime import date, timedelta
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import List, Optional
from pydantic import ValidationError
from models import Asset, AssetCreate, AssetUpdate, Criticality

app = FastAPI(title="Asset Management API")

assets_db: dict[str, Asset] = {}

def generate_sample_csv(csv_path: str):
    asset_types = ["Pump", "Valve", "Motor", "Compressor", "Turbine", "Fan", "Heat Exchanger"]
    units = [f"U{i}" for i in range(1, 11)]
    locations = [f"Building {chr(65+i)}" for i in range(10)]
    statuses = ["Active", "Inactive", "Maintenance", "Retired"]
    criticalities = ["High", "Medium", "Low"]
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["asset_id", "asset_type", "unit", "location", "install_year", "last_inspection", "operating_hours", "status", "criticality", "notes"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i in range(60):
            asset_id = f"AST-{1000+i}"
            writer.writerow({
                "asset_id": asset_id,
                "asset_type": random.choice(asset_types),
                "unit": random.choice(units),
                "location": random.choice(locations),
                "install_year": random.randint(1990, 2023),
                "last_inspection": (date.today() - timedelta(days=random.randint(1, 365))).isoformat(),
                "operating_hours": round(random.uniform(100, 50000), 1),
                "status": random.choice(statuses),
                "criticality": random.choice(criticalities),
                "notes": f"Sample asset {i+1}"
            })

def load_assets_from_csv():
    csv_path = os.path.join(os.path.dirname(__file__), "maintenance_assets.csv")
    if not os.path.exists(csv_path):
        generate_sample_csv(csv_path)
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row['criticality'] = Criticality(row['criticality'])
            row['install_year'] = int(row['install_year'])
            row['operating_hours'] = float(row['operating_hours'])
            asset = Asset(**row, deleted=False)
            assets_db[asset.asset_id] = asset

@app.on_event("startup")
def load_assets():
    load_assets_from_csv()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])
        errors.append({"field": field, "reason": error["msg"]})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"errors": errors},
    )

@app.post("/assets", response_model=Asset, status_code=status.HTTP_201_CREATED)
def create_asset(asset: AssetCreate):
    if asset.asset_id in assets_db:
        raise HTTPException(status_code=400, detail="Asset ID already exists")
    new_asset = Asset(**asset.model_dump(), deleted=False)
    assets_db[asset.asset_id] = new_asset
    return new_asset

@app.get("/assets", response_model=List[Asset])
def list_assets(
    status: Optional[str] = Query(None),
    unit: Optional[str] = Query(None),
    criticality: Optional[Criticality] = Query(None)
):
    filtered = [asset for asset in assets_db.values() if not asset.deleted]
    if status:
        filtered = [a for a in filtered if a.status == status]
    if unit:
        filtered = [a for a in filtered if a.unit == unit]
    if criticality:
        filtered = [a for a in filtered if a.criticality == criticality]
    return filtered

@app.get("/assets/{asset_id}", response_model=Asset)
def get_asset(asset_id: str):
    asset = assets_db.get(asset_id)
    if not asset or asset.deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@app.put("/assets/{asset_id}", response_model=Asset)
async def update_asset(asset_id: str, request: Request):
    asset = assets_db.get(asset_id)

    if not asset or asset.deleted:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

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
            detail=[
                {
                    "field": ".".join(map(str, e["loc"])),
                    "reason": e["msg"]
                }
                for e in exc.errors()
            ]
        ) from exc
    update_data = asset_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(asset, field, value)

    assets_db[asset_id] = asset
    return asset

@app.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(asset_id: str):
    asset = assets_db.get(asset_id)
    if not asset or asset.deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
    asset.deleted = True
    assets_db[asset_id] = asset
    return None
