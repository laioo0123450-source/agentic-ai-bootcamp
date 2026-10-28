

```python
# models.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import date

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
        if not r'^[A-Z]{3}-\d{4}$'.match(v):
            raise ValueError('asset_id must follow XXX-nnnn format')
        return v
```

```python
# main.py
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import List, Optional
import csv
from models import Asset, AssetCreate, AssetUpdate

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
                last_inspection=row['last_inspection'],
                operating_hours=float(row['operating_hours']),
                status=row['status'],
                criticality=row['criticality'],
                notes=row.get('notes')
            )
            assets_db[asset.asset_id] = asset

load_assets()

# Exception handler for validation errors
@app.exception_handler(ValidationError)
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
async def update_asset(asset_id: str, asset_update: AssetUpdate):
    asset = get_asset(asset_id)
    update_data = asset_update.dict(exclude_unset=True)
    
    # Prevent asset_id modification
    if 'asset_id' in update_data:
        raise HTTPException(status_code=400, detail="Cannot modify asset_id")
    
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
```

```python
# test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app
from models import Asset, AssetCreate, AssetUpdate
from datetime import date

client = TestClient(app)

def test_create_asset_success():
    response = client.post("/assets", json={
        "asset_id": "TEST-0001",
        "asset_type": "Pump",
        "unit": "Unit-A",
        "location": "Building-1",
        "install_year": 2020,
        "last_inspection": "2023-01-01",
        "operating_hours": 1000.5,
        "status": "Active",
        "criticality": "High",
        "notes": "Test asset"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == "TEST-0001"

def test_create_asset_failure_invalid_id():
    response = client.post("/assets", json={
        "asset_id": "invalid-id",
        "asset_type": "Pump",
        "unit": "Unit-A",
        "location": "Building-1",
        "install_year": 2020,
        "last_inspection": "2023-01-01",
        "operating_hours": 1000.5,
        "status": "Active",
        "criticality": "High"
    })
    assert response.status_code == 422
    assert "errors" in response.json()

def test_list_assets_success():
    response = client.get("/assets")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_list_assets_with_filters():
    response = client.get("/assets?status=Active&criticality=High")
    assert response.status_code == 200
    for asset in response.json():
        assert asset["status"] == "Active"
        assert asset["criticality"] == "High"

def test_retrieve_asset_success():
    response = client.get("/assets/TEST-0001")
    assert response.status_code == 200
    assert response.json()["asset_id"] == "TEST-0001"

def test_retrieve_asset_not_found():
    response = client.get("/assets/NON-EXIST")
    assert response.status_code == 404

def test_update_asset_success():
    response = client.put("/assets/TEST-0001", json={
        "location": "Building-2"
    })
    assert response.status_code == 200
    assert response.json()["location"] == "Building-2"

def test_update_asset_failure_modify_id():
    response = client.put("/assets/TEST-0001", json={
        "asset_id": "NEW-0001"
    })
    assert response.status_code == 400

def test_delete_asset_success():
    # Create a new asset for deletion
    client.post("/assets", json={
        "asset_id": "DEL-0001",
        "asset_type": "Pump",
        "unit": "Unit-A",
        "location": "Building-1",
        "install_year": 2020,
        "last_inspection": "2023-01-01",
        "operating_hours": 1000.5,
        "status": "Active",
        "criticality": "High"
    })
    
    response = client.delete("/assets/DEL-0001")
    assert response.status_code == 200
    
    # Verify soft deletion
    get_response = client.get("/assets/DEL-0001")
    assert get_response.status_code == 404

def test_delete_asset_not_found():
    response = client.delete("/assets/NON-EXIST")
    assert response.status_code == 404
```

```markdown
# Asset Management API

## Overview
A FastAPI-based CRUD API for managing industrial maintenance asset records.

## Requirements
- Python 3.8+
- FastAPI
- Pydantic v2
- pytest

## Installation
```bash
pip install fastapi uvicorn pytest pydantic
```

## Usage
1. Start the server:
```bash
uvicorn main:app --reload
```

2. Run tests:
```bash
pytest -q
```

## API Endpoints
- `POST /assets` - Create a new asset
- `GET /assets` - List assets with optional filters (status, unit, criticality)
- `GET /assets/{asset_id}` - Retrieve a specific asset
- `PUT /assets/{asset_id}` - Update an asset
- `DELETE /assets/{asset_id}` - Delete an asset (soft delete by default)

## Validation
- Asset ID must follow XXX-nnnn format (e.g., PMP-0001)
- Criticality must be one of: High, Medium, Low
- Asset ID cannot be modified during updates
- Install year must be between 1900 and 2100
- Operating hours must be non-negative

## CSV Data
The API automatically loads 60 records from `maintenance_assets.csv` at startup.
```

```csv
# maintenance_assets.csv (sample - include 60 records)
asset_id,asset_type,unit,location,install_year,last_inspection,operating_hours,status,criticality,notes
PMP-0001,Pump,Unit-A,Building-1,2020,2023-01-01,1000.5,Active,High,Primary cooling pump
PMP-0002,Pump,Unit-B,Building-2,2019,2023-02-15,850.3,Active,Medium,Backup pump
PMP-0003,Valve,Unit-C,Building-3,2021,2023-03-10,200.0,Inactive,Low,Isolation valve
PMP-0004,Motor,Unit-A,Building-1,2018,2023-01-20,1500.7,Active,High,Drive motor
PMP-0005,Compressor,Unit-D,Building-4,2022,2023-04-05,300.2,Active,Medium,Air compressor
PMP-0006,Heat Exchanger,Unit-B,Building-2,2017,2023-02-28,2200.1,Active,High,Main heat exchanger
PMP-0007,Pump,Unit-E,Building-5,2020,2023-03-15,750.8,Active,Low,Secondary pump
PMP-0008,Sensor,Unit-C,Building-3,2021,2023-04-10,100.0,Active,Medium,Pressure sensor
PMP-0009,Valve,Unit-A,Building-1,2019,2023-01-25,150.5,Inactive,Low,Control valve
PMP-0010,Motor,Unit-D,Building-4,2020,2023-02-10,1200.3,Active,High,Conveyor motor
PMP-0011,Compressor,Unit-B,Building-2,2021,2023-03-20,400.7,Active,Medium,Refrigeration compressor
PMP-0012,Pump,Unit-C,Building-3,2018,2023-01-30,900.2,Active,Medium,Booster pump
PMP-0013,Heat Exchanger,Unit-E,Building-5,2022,2023-04-15,1800.5,Active,High,Oil cooler
PMP-0014,Sensor,Unit-A,Building-1,2020,2023-02-05,50.0,Active,Low,Temperature sensor
PMP-0015,Valve,Unit-D,Building-4,2019,2023-03-25,125.8,Inactive,Low,Relief valve
PMP-0016,Motor,Unit-C,Building-3,2021,2023-04-20,1100.9,Active,High,Pump motor
PMP-0017,Compressor,Unit-E,Building-5,2018,2023-01-15,350.4,Active,Medium,Gas compressor
PMP-0018,Pump,Unit-B,Building-2,2020,2023-02-20,850.6,Active,Low,Circulation pump
PMP-0019,Heat Exchanger,Unit-C,Building-3,2019,2023-03-30,2100.3,Active,High,Condenser
PMP-0020,Sensor,Unit-D,Building-4,2021,2023-04-25,75.0,Active,Medium,Flow sensor
PMP-0021,Valve,Unit-E,Building-5,2020,2023-01-10,175.2,Inactive,Low,Gate valve
PMP-0022,Motor,Unit-B,Building-2,2018,2023-02-25,1300.1,Active,High,Fan motor
PMP-0023,Compressor,Unit-C,Building-3,2021,2023-03-05,450.8,Active,Medium,Vacuum compressor
PMP-0024,Pump,Unit-A,Building-1,2019,2023-04-30,950.4,Active,Low,Drainage pump
PMP-0025,Heat Exchanger,Unit-D,Building-4,2020,2023-01-20,1950.7,Active,High,Cooler
PMP-0026,Sensor,Unit-B,Building-2,2021,2023-02-28,60.0,Active,Low,Vibration sensor
PMP-0027,Valve,Unit-C,Building-3,2018,2023-03-15,140.9,Inactive,Low,Needle valve
PMP-0028,Motor,Unit-E,Building-5,2020,2023-04-10,1150.2,Active,High,Agitator motor
PMP-0029,Compressor,Unit-A,Building-1,2019,2023-01-25,380.6,Active,Medium,Booster compressor
PMP-0030,Pump,Unit-D,Building-4,2021,2023-02-15,875.3,Active,Medium,Feed pump
PMP-0031,Heat Exchanger,Unit-B,Building-2,2018,2023-03-20,2050.9,Active,High,Heater
PMP-0032,Sensor,Unit-E,Building-5,2020,2023-04-05,55.0,Active,Low,Level sensor
PMP-0033,Valve,Unit-A,Building-1,2021,2023-01-30,185.4,Inactive,Low,Butterfly valve
PMP-0034,Motor,Unit-C,Building-3,2019,2023-02-10,1250.8,Active,High,Crusher motor
PMP-0035,Compressor,Unit-D,Building-4,2020,2023-03-25,420.1,Active,Medium,Scroll compressor
PMP-0036,Pump,Unit-E,Building-5,2018,2023-04-15,925.6,Active,Low,Sludge pump
PMP-0037,Heat Exchanger,Unit-A,Building-1,2021,2023-01-15,1900.3,Active,High,Chiller
PMP-0038,Sensor,Unit-C,Building-3,2019,2023-02-20,65.0,Active,Medium,Conductivity sensor
PMP-0039,Valve,Unit-B,Building-2,2020,2023-03-30,155.7,Inactive,Low,Check valve
PMP-0040,Motor,Unit-D,Building-4,2018,2023-04-20,1400.5,Active,High,Conveyor motor
PMP-0041,Compressor,Unit-E,Building-5,2021,2023-01-10,470.9,Active,Medium,Piston compressor
PMP-0042,Pump,Unit-C,Building-3,2019,2023-02-05,890.2,Active,Low,Chemical dosing pump
PMP-0043,Heat Exchanger,Unit-B,Building-2,2020,2023-03-15,2000.1,Active,High,Evaporator
PMP-0044,Sensor,Unit-A,Building-1,2021,2023-04-25,70.0,Active,Low,pH sensor
PMP-0045,Valve,Unit-D,Building-4,2018,2023-01-20,165.3,Inactive,Low,Ball valve
PMP-0046,Motor,Unit-E,Building-5,2020,2023-02-15,1300.7,Active,High,Crusher motor
PMP-0047,Compressor,Unit-C,Building-3,2019,2023-03-25,430.4,Active,Medium,Screw compressor
PMP-0048,Pump,Unit-B,Building-2,2021,2023-04-10,940.9,Active,Medium,Slurry pump
PMP-0049,Heat Exchanger,Unit-D,Building-4,2018,2023-01-30,1950.2,Active,High,Condenser
PMP-0050,Sensor,Unit-E,Building-5,2020,2023-02-28,80.0,Active,Medium,Pressure transmitter
PMP-0051,Valve,Unit-A,Building-1,2021,2023-03-10,190.6,Inactive,Low,Globe valve
PMP-0052,Motor,Unit-C,Building-3,2019,2023-04-15,1350.1,Active,High,Blower motor
PMP-0053,Compressor,Unit-B,Building-2,2020,2023-01-25,460.3,Active,Medium,Diaphragm compressor
PMP-0054,Pump,Unit-D,Building-4,2018,2023-02-10,900.8,Active,Low,Chemical pump
PMP-0055,Heat Exchanger,Unit-E,Building-5,2021,2023-03-20,2100.4,Active,High,Boiler
PMP-0056,Sensor,Unit-A,Building-1,2019,2023-04-30,85.0,Active,Low,Flow meter
PMP-0057,Valve,Unit-C,Building-3,2020,2023-01-15,170.9,Inactive,Low,Pinch valve
PMP-0058,Motor,Unit-B,Building-2,2018,2023-02-20,1450.6,Active,High,Extruder motor
PMP-0059,Compressor,Unit-D,Building-4,2021,2023-03-05,440.2,Active,Medium,Turbo compressor
PMP-0060,Pump,Unit-E,Building-5,2019,2023-04-10,955.7,Active,Medium,Condensate pump
```