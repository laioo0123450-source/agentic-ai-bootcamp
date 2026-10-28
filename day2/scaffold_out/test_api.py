import pytest
import csv
import os
from datetime import datetime
from fastapi.testclient import TestClient

# Create a test CSV file with sample data
TEST_CSV = """asset_id,asset_type,unit,location,install_year,last_inspection,operating_hours,status,criticality,notes,flagged
ABC-1234,Pump,A-100,Room 101,2020,1/15/2024,5000,Active,High,Test asset,true
DEF-5678,Valve,B-200,Room 102,2021,2/20/2024,3000,Inactive,Medium,Another asset,false
GHI-9012,Compressor,C-300,Room 103,2019,3/10/2024,8000,Active,Low,Third asset,true
"""

@pytest.fixture
def test_csv_file(tmp_path):
    csv_file = tmp_path / "test_assets.csv"
    with open(csv_file, 'w', newline='') as f:
        f.write(TEST_CSV)
    return str(csv_file)

@pytest.fixture
def client(test_csv_file, monkeypatch):
    monkeypatch.setenv('CSV_FILE_PATH', test_csv_file)
    from main import app
    with TestClient(app) as client:
        yield client

# Tests

def test_create_asset(client):
    response = client.post("/assets", json={
        "asset_id": "JKL-3456",
        "asset_type": "Motor",
        "unit": "D-400",
        "location": "Room 104",
        "install_year": 2022,
        "last_inspection": "5/5/2024",
        "operating_hours": 1000,
        "status": "Active",
        "criticality": "High",
        "notes": "New motor"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["asset_id"] == "JKL-3456"

def test_create_asset_invalid_id(client):
    response = client.post("/assets", json={
        "asset_id": "invalid",
        "asset_type": "Motor",
        "unit": "D-400",
        "location": "Room 104",
        "install_year": 2022,
        "last_inspection": "5/5/2024",
        "operating_hours": 1000,
        "status": "Active",
        "criticality": "High"
    })
    assert response.status_code == 422
    data = response.json()
    assert "errors" in data
    assert any(e["field"] == "asset_id" for e in data["errors"])

def test_list_assets(client):
    response = client.get("/assets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3

def test_list_assets_with_filter(client):
    response = client.get("/assets?status=Active")
    assert response.status_code == 200
    data = response.json()
    for asset in data:
        assert asset["status"] == "Active"

def test_get_asset(client):
    response = client.get("/assets/ABC-1234")
    assert response.status_code == 200
    data = response.json()
    assert data["asset_id"] == "ABC-1234"

def test_get_asset_not_found(client):
    response = client.get("/assets/XXX-0000")
    assert response.status_code == 404

def test_update_asset(client):
    response = client.put("/assets/ABC-1234", json={
        "asset_type": "Pump Updated",
        "unit": "A-100",
        "location": "Room 101",
        "install_year": 2020,
        "last_inspection": "1/15/2024",
        "operating_hours": 5000,
        "status": "Active",
        "criticality": "High",
        "notes": "Updated notes"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["asset_type"] == "Pump Updated"

def test_update_asset_with_id_in_body(client):
    response = client.put("/assets/ABC-1234", json={
        "asset_id": "ABC-1234",
        "asset_type": "Pump Updated",
        "unit": "A-100",
        "location": "Room 101",
        "install_year": 2020,
        "last_inspection": "1/15/2024",
        "operating_hours": 5000,
        "status": "Active",
        "criticality": "High"
    })
    assert response.status_code == 400

def test_update_asset_invalid_criticality(client):
    response = client.put("/assets/ABC-1234", json={
        "asset_type": "Pump Updated",
        "unit": "A-100",
        "location": "Room 101",
        "install_year": 2020,
        "last_inspection": "1/15/2024",
        "operating_hours": 5000,
        "status": "Active",
        "criticality": "Invalid",
        "notes": "Test"
    })
    assert response.status_code == 422

def test_delete_asset(client):
    response = client.delete("/assets/ABC-1234")
    assert response.status_code == 204
    # Verify it's gone
    response = client.get("/assets/ABC-1234")
    assert response.status_code == 404

def test_delete_asset_not_found(client):
    response = client.delete("/assets/XXX-0000")
    assert response.status_code == 404

def test_duplicate_asset_id(client):
    response = client.post("/assets", json={
        "asset_id": "ABC-1234",
        "asset_type": "Pump",
        "unit": "A-100",
        "location": "Room 101",
        "install_year": 2020,
        "last_inspection": "1/15/2024",
        "operating_hours": 5000,
        "status": "Active",
        "criticality": "High"
    })
    assert response.status_code == 400

def test_soft_deleted_not_in_list(client):
    # Delete an asset
    client.delete("/assets/ABC-1234")
    # List assets should not include it
    response = client.get("/assets")
    data = response.json()
    ids = [a["asset_id"] for a in data]
    assert "ABC-1234" not in ids

def test_flagged_filter(client):
    response = client.get("/assets?flagged=true")
    assert response.status_code == 200
    data = response.json()
    for asset in data:
        assert asset["flagged"] == True
