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
