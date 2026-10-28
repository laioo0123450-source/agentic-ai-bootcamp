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


def test_reject_asset_id_change():
    asset_id = get_existing_asset_id()

    response = client.put(
        f"/assets/{asset_id}",
        json={"asset_id": "NEW-0001"}
    )

    assert response.status_code == 400
