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
