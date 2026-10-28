# Asset Maintenance Mini-App

A FastAPI CRUD backend for industrial maintenance assets, with a simple HTML frontend for viewing flagged assets.

## Requirements

- Python 3.12
- FastAPI
- Pydantic v2
- Uvicorn (for running the server)
- pytest (for testing)

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn pydantic pytest
   ```

## Running the Server

Start the FastAPI server with:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. The interactive documentation is at `/docs`.

## Running the Tests

Run the test suite with:
```bash
pytest -q
```

## Data

The application loads data from `maintenance_assets.csv` on startup. The CSV file should have the following columns:
- asset_id
- asset_type
- unit
- location
- install_year
- last_inspection (M/D/YYYY format)
- operating_hours
- status
- criticality
- notes (optional)
- flagged (optional boolean)

If the CSV file is missing, the application will start with an empty database.

## API Endpoints

- `POST /assets` - Create a new asset.
- `GET /assets` - List assets with optional filters: `status`, `unit`, `criticality`, `flagged`.
- `GET /assets/{asset_id}` - Retrieve a single asset.
- `PUT /assets/{asset_id}` - Update an asset.
- `DELETE /assets/{asset_id}` - Soft-delete an asset.

## HTML UI

Open `index.html` in a web browser to view the list of flagged assets. The page fetches data from `/assets?flagged=true`.

## Notes

- Asset IDs must match the pattern `^[A-Z]{3}-\d{4}$`.
- Criticality must be one of: High, Medium, Low.
- Asset IDs are immutable and cannot be modified.
- Duplicate asset IDs are rejected.
- Soft-deleted assets are excluded from GET results.
