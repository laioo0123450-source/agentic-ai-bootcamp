# Lab 1.2 — Target System: Asset Maintenance Records API

Build-target for your agent prompt template. Seed data: `maintenance_assets.csv` (60 records).

## Entity: Asset
`asset_id, asset_type, unit, location, install_year, last_inspection, operating_hours, status, criticality, notes`

## Required endpoints (CRUD)
- `POST /assets` — create (validate asset_id format `XXX-nnnn`, criticality in {High, Medium, Low})
- `GET /assets` — list, with filters: `?status=`, `?unit=`, `?criticality=`
- `GET /assets/{asset_id}` — read one (404 on missing)
- `PUT /assets/{asset_id}` — update (reject changes to asset_id)
- `DELETE /assets/{asset_id}` — delete (soft-delete preferred)

## Non-functional requirements (the part agents usually miss)
- FastAPI + Pydantic models, typed; CSV load on startup
- Input validation errors return structured JSON (field, reason)
- Unit tests with pytest for every endpoint (happy path + 1 failure case each)
- README with run instructions

## Prompt-template evaluation checklist (per LLM: GPT-4 / Claude / LLaMA / Mistral)
| Check | Pass? |
|---|---|
| All 5 endpoints generated | |
| Validation rules enforced | |
| Tests generated and passing | |
| Runs without manual fixes | |
| # of manual interventions needed | |
→ "Where does the tool fall short of autonomy?" = the interventions column.
