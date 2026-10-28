```python
# main.py
import os
import csv
import random
from datetime import date, timedelta
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import List, Optional
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
def update_asset(asset_id: str, asset_update: AssetUpdate):
    asset = assets_db.get(asset_id)
    if not asset or asset.deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
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
```

```python
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
```

```python
# test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app, assets_db, load_assets_from_csv

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    assets_db.clear()
    load_assets_from_csv()
    yield

def get_existing_asset_id():
    response = client.get("/assets")
    assert response.status_code == 200
    assets = response.json()
    assert len(assets) > 0
    return assets[0]["asset_id"]

def test_create_asset_success():
    new_asset = {
        "asset_id": "ABC-1234",
        "asset_type": "Pump",
        "unit": "U1",
        "location": "Building A",
        "install_year": 2020,
        "last_inspection": "2023-01-15",
        "operating_hours": 5000.0,
        "status": "Active",
        "criticality": "High",
        "notes": "Test asset"
    }
    response = client.post("/assets", json=new_asset)
    assert response.status_code == 201
    data = response.json()
    assert data["asset_id"] == "ABC-1234"
    assert data["deleted"] == False

def test_create_asset_failure_invalid_id_format():
    new_asset = {
        "asset_id": "INVALID-ID",
        "asset_type": "Pump",
        "unit": "U1",
        "location": "Building A",
        "install_year": 2020,
        "last_inspection": "2023-01-15",
        "operating_hours": 5000.0,
        "status": "Active",
        "criticality": "High",
        "notes": "Test asset"
    }
    response = client.post("/assets", json=new_asset)
    assert response.status_code == 422
    errors = response.json()["errors"]
    assert any(e["field"] == "asset_id" for e in errors)

def test_create_asset_failure_duplicate_id():
    new_asset = {
        "asset_id": "XYZ-9999",
        "asset_type": "Valve",
        "unit": "U2",
        "location": "Building B",
        "install_year": 2019,
        "last_inspection": "2022-06-10",
        "operating_hours": 3000.0,
        "status": "Active",
        "criticality": "Medium",
        "notes": "Duplicate test"
    }
    client.post("/assets", json=new_asset)
    response = client.post("/assets", json=new_asset)
    assert response.status_code == 400
    assert response.json()["detail"] == "Asset ID already exists"

def test_list_assets_success():
    response = client.get("/assets")
    assert response.status_code == 200
    assets = response.json()
    assert isinstance(assets, list)
    assert len(assets) >= 60

def test_list_assets_with_filters():
    response = client.get("/assets?status=Active")
    assert response.status_code == 200
    assets = response.json()
    for asset in assets:
        assert asset["status"] == "Active"

def test_get_asset_success():
    asset_id = get_existing_asset_id()
    response = client.get(f"/assets/{asset_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == asset_id

def test_get_asset_failure_not_found():
    response = client.get("/assets/NONEXISTENT-0000")
    assert response.status_code == 404

def test_update_asset_success():
    asset_id = get_existing_asset_id()
    update_data = {
        "status": "Inactive",
        "notes": "Updated via test"
    }
    response = client.put(f"/assets/{asset_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Inactive"
    assert data["notes"] == "Updated via test"

def test_update_asset_failure_not_found():
    update_data = {"status": "Inactive"}
    response = client.put("/assets/NONEXISTENT-0000", json=update_data)
    assert response.status_code == 404

def test_update_asset_failure_invalid_criticality():
    asset_id = get_existing_asset_id()
    update_data = {"criticality": "Invalid"}
    response = client.put(f"/assets/{asset_id}", json=update_data)
    assert response.status_code == 422

def test_delete_asset_success():
    new_asset = {
        "asset_id": "DEL-0001",
        "asset_type": "Motor",
        "unit": "U3",
        "location": "Building C",
        "install_year": 2021,
        "last_inspection": "2023-03-01",
        "operating_hours": 1000.0,
        "status": "Active",
        "criticality": "Low",
        "notes": "To be deleted"
    }
    client.post("/assets", json=new_asset)
    response = client.delete("/assets/DEL-0001")
    assert response.status_code == 204
    get_response = client.get("/assets/DEL-0001")
    assert get_response.status_code == 404

def test_delete_asset_failure_not_found():
    response = client.delete("/assets/NONEXISTENT-0000")
    assert response.status_code == 404
```

```markdown
# README.md
# Asset Management API

A FastAPI CRUD API for industrial maintenance assets.

## Requirements

- Python 3.9+
- FastAPI
- Uvicorn
- Pydantic v2
- pytest

## Installation

```bash
pip install fastapi uvicorn pydantic pytest
```

## Data File

Place `maintenance_assets.csv` in the project root directory. The CSV must contain the following columns:
- asset_id
- asset_type
- unit
- location
- install_year
- last_inspection
- operating_hours
- status
- criticality
- notes

The `asset_id` must follow the format `XXX-nnnn` (three letters, hyphen, four digits).
The `criticality` must be one of: `High`, `Medium`, `Low`.

If the file is missing at startup, a sample CSV with 60 records will be generated automatically.

## Running the API

Start the server with Uvicorn:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | /assets  | Create a new asset |
| GET    | /assets  | List assets (supports `status`, `unit`, `criticality` query filters) |
| GET    | /assets/{asset_id} | Retrieve a single asset |
| PUT    | /assets/{asset_id} | Update an asset (asset_id cannot be changed) |
| DELETE | /assets/{asset_id} | Soft delete an asset |

## Validation

- `asset_id` must match regex `^[A-Za-z]{3}-\d{4}$`.
- `criticality` must be `High`, `Medium`, or `Low`.
- Validation errors return a structured JSON response:
  ```json
  {
    "errors": [
      { "field": "asset_id", "reason": "string does not match pattern" },
      ...
    ]
  }
  ```

## Running Tests

Execute pytest:

```bash
pytest -q
```

Tests cover success and failure cases for each endpoint.
```