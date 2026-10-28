
# PROMPT TEMPLATE — CRUD API Builder (v1.0)

ROLE:
You are a senior Python backend engineer who writes production-quality, fully tested code.

TASK:
Build a complete, runnable CRUD API for the following entity.

STACK: FastAPI + Pydantic v2

ENTITY: Asset (industrial maintenance record)

FIELDS:
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

ENDPOINTS:
1. POST /assets — create an asset.
2. GET /assets — list assets with status, unit, and criticality filters.
3. GET /assets/{asset_id} — retrieve an asset; return 404 if missing.
4. PUT /assets/{asset_id} — update an asset; reject asset_id changes.
5. DELETE /assets/{asset_id} — delete an asset; prefer soft deletion.

VALIDATION:
- asset_id must follow XXX-nnnn format.
- criticality must be High, Medium, or Low.
- asset_id must not be modified during updates.
- Return structured JSON validation errors containing field and reason.

DATA:
Load maintenance_assets.csv (60 records) at startup.

TESTS:
Use pytest. Include at least one successful test and one failure test for every endpoint.

OUTPUT FORMAT:
Provide one fenced code block per file, preceded by its file path.

Required files:
- main.py
- models.py
- test_api.py
- README.md

Do not include prose between files.

DEFINITION OF DONE:
- uvicorn main:app starts successfully.
- pytest -q passes.
- No TODOs or placeholders.
