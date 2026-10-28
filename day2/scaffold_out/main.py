import csv
import re
import os
from datetime import datetime
from datetime import date
from contextlib import asynccontextmanager
from typing import Optional, List, Any
from fastapi import FastAPI, HTTPException, Query, Request, status
from pydantic import BaseModel, field_validator, ValidationError
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Settings
def get_csv_file_path():
    return os.environ.get('CSV_FILE_PATH', 'maintenance_assets.csv')

# Pydantic models
class AssetBase(BaseModel):
    asset_type: str
    unit: str
    location: str
    install_year: int
    last_inspection: date
    operating_hours: int
    status: str
    criticality: str
    notes: Optional[str] = None

    @field_validator("criticality")
    @classmethod
    def validate_criticality(cls, v):
        if v not in ["High", "Medium", "Low"]:
            raise ValueError("Criticality must be High, Medium, or Low")
        return v

    @field_validator("last_inspection", mode="before")
    @classmethod
    def parse_last_inspection(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%m/%d/%Y').date()
            except ValueError:
                return datetime.strptime(v, '%Y-%m-%d').date()
        return v

class AssetCreate(AssetBase):
    asset_id: str

    @field_validator("asset_id")
    @classmethod
    def validate_asset_id(cls, v):
        if not re.match(r"^[A-Z]{3}-\d{4}$", v):
         raise ValueError(r"Asset ID must match pattern ^[A-Z]{3}-\d{4}$")
        return v

class AssetUpdate(AssetBase):
    pass

class Asset(AssetBase):
    asset_id: str
    flagged: Optional[bool] = None
    deleted: bool = False

# In-memory storage
assets_db: List[Asset] = []

def load_assets_from_csv(file_path: str):
    global assets_db
    assets_db = []
    try:
        with open(file_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert types
                row['install_year'] = int(row['install_year'])
                row['operating_hours'] = int(row['operating_hours'])
                # Parse date
                row['last_inspection'] = datetime.strptime(row['last_inspection'], '%m/%d/%Y').date()
                # Create Asset
                asset_data = {
                    'asset_id': row['asset_id'],
                    'asset_type': row['asset_type'],
                    'unit': row['unit'],
                    'location': row['location'],
                    'install_year': row['install_year'],
                    'last_inspection': row['last_inspection'],
                    'operating_hours': row['operating_hours'],
                    'status': row['status'],
                    'criticality': row['criticality'],
                    'notes': row.get('notes', ''),
                }
                if 'flagged' in row:
                    asset_data['flagged'] = row['flagged'].lower() == 'true'
                asset = Asset(**asset_data)
                assets_db.append(asset)
    except FileNotFoundError:
        raise RuntimeError(f"CSV file not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to load CSV: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        load_assets_from_csv(get_csv_file_path())
    except RuntimeError as e:
        print(f"Error loading CSV: {e}")
        # Continue with empty database
    yield

app = FastAPI(lifespan=lifespan)

# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "errors": [
                {
                    "field": ".".join(str(p) for p in err["loc"] if p != "body"),
                    "reason": str(err["msg"])
                }
                for err in exc.errors()
            ]
        }
    )
# CRUD endpoints

@app.post("/assets", response_model=Asset, status_code=status.HTTP_201_CREATED)
def create_asset(asset: AssetCreate):
    # Check duplicate
    for a in assets_db:
        if a.asset_id == asset.asset_id:
            raise HTTPException(status_code=400, detail="Asset ID already exists")
    new_asset = Asset(**asset.model_dump())
    assets_db.append(new_asset)
    return new_asset

@app.get("/assets", response_model=List[Asset])
def list_assets(
    status: Optional[str] = Query(None),
    unit: Optional[str] = Query(None),
    criticality: Optional[str] = Query(None),
    flagged: Optional[bool] = Query(None)
):
    results = [a for a in assets_db if not a.deleted]
    if status:
        results = [a for a in results if a.status == status]
    if unit:
        results = [a for a in results if a.unit == unit]
    if criticality:
        results = [a for a in results if a.criticality == criticality]
    if flagged is not None:
        results = [a for a in results if a.flagged == flagged]
    return results

@app.get("/assets/{asset_id}", response_model=Asset)
def get_asset(asset_id: str):
    for a in assets_db:
        if a.asset_id == asset_id and not a.deleted:
            return a
    raise HTTPException(status_code=404, detail="Asset not found")

@app.put("/assets/{asset_id}", response_model=Asset)
async def update_asset(request: Request, asset_id: str):
    body = await request.json()
    if 'asset_id' in body:
        raise HTTPException(status_code=400, detail="Asset ID cannot be modified")
    # Validate with AssetUpdate
    try: 
        asset_update = AssetUpdate(**body)
    except ValidationError as exc:
        return JSONResponse(
            status_code=422,
            content={
                "errors": [
                    {
                        "field": ".".join(str(p) for p in err["loc"]),
                        "reason": str(err["msg"])
                    }
                 for err in exc.errors()
                ]
            }
        )
    # Find asset
        # Find asset
    for a in assets_db:
        if a.asset_id == asset_id and not a.deleted:
            a.asset_type = asset_update.asset_type
            a.unit = asset_update.unit
            a.location = asset_update.location
            a.install_year = asset_update.install_year
            a.last_inspection = asset_update.last_inspection
            a.operating_hours = asset_update.operating_hours
            a.status = asset_update.status
            a.criticality = asset_update.criticality
            a.notes = asset_update.notes
            return a

    raise HTTPException(status_code=404, detail="Asset not found")

@app.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(asset_id: str):
    for a in assets_db:
        if a.asset_id == asset_id and not a.deleted:
            a.deleted = True
            return
    raise HTTPException(status_code=404, detail="Asset not found")
