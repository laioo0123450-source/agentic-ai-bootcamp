import pytest
from fastapi.testclient import TestClient
from main import app
from models import Asset, AssetCreate, AssetUpdate
from datetime import date

client = TestClient(app)

def test_create_asset_success():
    response = client.post("/assets", json={
        "asset_id": "TST-0001",
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
    assert data["asset_id"] == "TST-0001"

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
    response = client.get("/assets/TST-0001")
    assert response.status_code == 200
    assert response.json()["asset_id"] == "TST-0001"

def test_retrieve_asset_not_found():
    response = client.get("/assets/NON-EXIST")
    assert response.status_code == 404

def test_update_asset_success():
    response = client.put("/assets/TST-0001", json={
        "location": "Building-2"
    })
    assert response.status_code == 200
    assert response.json()["location"] == "Building-2"

def test_update_asset_failure_modify_id():
    response = client.put("/assets/TST-0001", json={
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