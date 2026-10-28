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

