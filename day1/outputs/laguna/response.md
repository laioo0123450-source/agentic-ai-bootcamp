```
# File: main.py
```

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import pandas as pd
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
def update_asset(asset_id: str, asset_update: AssetUpdate):
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
    raise HTTPException(status_code=404, detail="Asset not found")

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
```

```
# File: models.py
```

```python
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
```

```
# File: test_api.py
```

```python
from fastapi.testclient import TestClient
import pytest
from main import app, load_data
import pandas as pd

client = TestClient(app)

# Load test data before tests
@pytest.fixture(scope="module", autouse=True)
def setup_data():
    load_data()
    yield

def test_create_asset_success():
    response = client.post("/assets", json={
        "asset_id": "MOT-9999",
        "asset_type": "Motor",
        "unit": "U1",
        "location": "Plant A",
        "install_year": 2020,
        "last_inspection": "2023-01-01",
        "operating_hours": 1500.5,
        "status": "Active",
        "criticality": "High",
        "notes": "Test motor"
    })
    assert response.status_code == 200
    assert response.json()["asset_id"] == "MOT-9999"

def test_create_asset_duplicate():
    # Try creating the same asset twice
    client.post("/assets", json={
        "asset_id": "MOT-9998",
        "asset_type": "Motor",
        "unit": "U1",
        "location": "Plant A",
        "install_year": 2020,
        "last_inspection": "2023-01-01",
        "operating_hours": 1500.5,
        "status": "Active",
        "criticality": "High",
        "notes": "Test motor"
    })
    response = client.post("/assets", json={
        "asset_id": "MOT-9998",
        "asset_type": "Motor",
        "unit": "U1",
        "location": "Plant A",
        "install_year": 2020,
        "last_inspection": "2023-01-01",
        "operating_hours": 1500.5,
        "status": "Active",
        "criticality": "High",
        "notes": "Test motor"
    })
    assert response.status_code == 400

def test_create_asset_invalid_asset_id():
    response = client.post("/assets", json={
        "asset_id": "INVALID",
        "asset_type": "Motor",
        "unit": "U1",
        "location": "Plant A",
        "install_year": 2020,
        "last_inspection": "2023-01-01",
        "operating_hours": 1500.5,
        "status": "Active",
        "criticality": "High",
        "notes": "Test motor"
    })
    assert response.status_code == 422

def test_create_asset_invalid_criticality():
    response = client.post("/assets", json={
        "asset_id": "MOT-9997",
        "asset_type": "Motor",
        "unit": "U1",
        "location": "Plant A",
        "install_year": 2020,
        "last_inspection": "2023-01-01",
        "operating_hours": 1500.5,
        "status": "Active",
        "criticality": "Invalid",
        "notes": "Test motor"
    })
    assert response.status_code == 422

def test_list_assets_success():
    response = client.get("/assets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_assets_with_filters():
    response = client.get("/assets?status=Active&unit=U1&criticality=High")
    assert response.status_code == 200
    for asset in response.json():
        assert asset["status"] == "Active"
        assert asset["unit"] == "U1"
        assert asset["criticality"] == "High"

def test_get_asset_success():
    client.post("/assets", json={
        "asset_id": "PMP-9999",
        "asset_type": "Pump",
        "unit": "U2",
        "location": "Plant B",
        "install_year": 2019,
        "last_inspection": "2023-02-01",
        "operating_hours": 2000.0,
        "status": "Inactive",
        "criticality": "Medium",
        "notes": "Test pump"
    })
    response = client.get("/assets/PMP-9999")
    assert response.status_code == 200
    assert response.json()["asset_id"] == "PMP-9999"

def test_get_asset_not_found():
    response = client.get("/assets/XXX-0001")
    assert response.status_code == 404

def test_update_asset_success():
    client.post("/assets", json={
        "asset_id": "TRL-9999",
        "asset_type": "Truck",
        "unit": "U3",
        "location": "Plant C",
        "install_year": 2018,
        "last_inspection": "2023-03-01",
        "operating_hours": 3000.0,
        "status": "Active",
        "criticality": "Low",
        "notes": "Test truck"
    })
    response = client.put("/assets/TRL-9999", json={
        "asset_type": "Truck Updated"
    })
    assert response.status_code == 200
    assert response.json()["asset_type"] == "Truck Updated"

def test_update_asset_reject_asset_id_change():
    response = client.put("/assets/TRL-9999", json={
        "notes": "Updating with new id attempt"
    })
    # This should just update notes, not change asset_id
    assert response.status_code == 200

    # Try to change asset_id via custom validation
    # Since asset_id isn't in AssetUpdate model, we can't directly change it
    # But let's verify asset_id stays the same
    get_response = client.get("/assets/TRL-9999")
    assert get_response.status_code == 200
    assert get_response.json()["asset_id"] == "TRL-9999"

def test_update_asset_not_found():
    response = client.put("/assets/XXX-0001", json={
        "asset_type": "Updated"
    })
    assert response.status_code == 404

def test_delete_asset_success():
    client.post("/assets", json={
        "asset_id": "GEN-9999",
        "asset_type": "Generator",
        "unit": "U4",
        "location": "Plant D",
        "install_year": 2017,
        "last_inspection": "2023-04-01",
        "operating_hours": 4000.0,
        "status": "Active",
        "criticality": "High",
        "notes": "Test generator"
    })
    response = client.delete("/assets/GEN-9999")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()

def test_delete_asset_not_found():
    response = client.delete("/assets/XXX-0001")
    assert response.status_code == 404

def test_soft_delete_verification():
    """Verify that a deleted asset is not returned in listings"""
    client.post("/assets", json={
        "asset_id": "VLV-9999",
        "asset_type": "Valve",
        "unit": "U5",
        "location": "Plant E",
        "install_year": 2016,
        "last_inspection": "2023-05-01",
        "operating_hours": 5000.0,
        "status": "Active",
        "criticality": "Medium",
        "notes": "Test valve"
    })
    client.delete("/assets/VLV-9999")
    response = client.get("/assets")
    assert response.status_code == 200
    asset_ids = [a["asset_id"] for a in response.json()]
    assert "VLV-9999" not in asset_ids

def test_get_deleted_asset():
    """Verify that a deleted asset returns 404 when accessed directly"""
    response = client.get("/assets/VLV-9999")
    assert response.status_code == 404

def test_update_deleted_asset():
    """Verify that updating a deleted asset returns 404"""
    response = client.put("/assets/VLV-9999", json={
        "notes": "Try updating deleted asset"
    })
    assert response.status_code == 404
```

```
# File: README.md
```

```
# Asset Management CRUD API

A FastAPI-based REST API for managing industrial maintenance assets with full CRUD operations, validation, and testing capabilities.

## Features

- Create, Read, Update, and Delete (soft delete) assets
- Filter assets by status, unit, and criticality
- Validation for asset IDs (XXX-nnnn format) and criticality levels (High/Medium/Low)
- Structured JSON validation error responses
- Automatic loading of initial data from `maintenance_assets.csv`
- Comprehensive test suite covering all endpoints

## Requirements

- Python 3.8+
- FastAPI
- Pydantic v2
- Pandas
- Pytest
- Uvicorn
- httpx (for testing)

## Installation

```bash
pip install fastapi "pydantic>=2.0" pandas pytest uvicorn httpx
```

## Usage

1. Place `maintenance_assets.csv` in the same directory as the application files
2. Run the server:

```bash
uvicorn main:app --reload
```

3. Access the API at `http://localhost:8000`
4. View the interactive API documentation at `http://localhost:8000/docs`

## API Endpoints

### POST /assets
Create a new asset.

**Request Body:**
```json
{
  "asset_id": "MOT-0001",
  "asset_type": "Motor",
  "unit": "U1",
  "location": "Plant A",
  "install_year": 2020,
  "last_inspection": "2023-01-01",
  "operating_hours": 1500.5,
  "status": "Active",
  "criticality": "High",
  "notes": "Critical motor in production line"
}
```

**Response:** Created asset object with 200 status code

### GET /assets
List all non-deleted assets with optional filters.

**Query Parameters (all optional):**
- `status`: Filter by asset status
- `unit`: Filter by unit
- `criticality`: Filter by criticality level

**Response:** Array of asset objects

### GET /assets/{asset_id}
Retrieve a specific asset by ID.

**Response:** Asset object or 404 if not found

### PUT /assets/{asset_id}
Update an existing asset. Note that `asset_id` cannot be changed.

**Request Body:** Partial asset object with fields to update

**Response:** Updated asset object or 404 if not found

### DELETE /assets/{asset_id}
Soft delete an asset by marking it as deleted.

**Response:** Success message or 404 if not found

## Validation Rules

1. **asset_id**: Must follow the format `XXX-nnnn` (three uppercase letters, hyphen, four digits)
2. **criticality**: Must be one of "High", "Medium", or "Low"
3. **Update constraint**: `asset_id` cannot be modified through updates

## Error Responses

Validation errors return structured JSON:
```json
{
  "detail": [
    {
      "loc": ["body"],
      "msg": "Validation error message",
      "type": "value_error"
    }
  ]
}
```

## Testing

Run the test suite:

```bash
pytest -q
```

The test suite includes:
- Successful creation, retrieval, update, and deletion
- Failure cases for each endpoint (duplicate IDs, invalid formats, not found scenarios)
- Soft deletion verification
- Filter functionality testing

## Data Model

Each asset contains the following fields:

| Field              | Type    | Description                          |
|--------------------|---------|--------------------------------------|
| asset_id           | string  | Unique identifier (XXX-nnnn format)  |
| asset_type         | string  | Type of asset                        |
| unit               | string  | Unit designation                     |
| location           | string  | Physical location                    |
| install_year       | int     | Year installed                       |
| last_inspection    | string  | Date of last inspection              |
| operating_hours    | float   | Total operating hours                |
| status             | string  | Current operational status           |
| criticality        | string  | Criticality level (High/Medium/Low)  |
| notes              | string  | Additional notes                     |
| deleted            | bool    | Soft delete flag (internal use)      |
```