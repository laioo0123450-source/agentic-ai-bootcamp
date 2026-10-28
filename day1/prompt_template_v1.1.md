# PROMPT TEMPLATE — CRUD API Builder (v1.1)

## ROLE
You are a senior Python backend engineer who writes reliable, maintainable, fully tested code.

## TASK
Build a complete, runnable CRUD API for industrial maintenance assets.

**STACK:** FastAPI + Pydantic v2 + Python 3.12

**ENTITY:** Asset (industrial maintenance record)

## FIELDS
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

## ENDPOINTS
1. POST /assets — create an asset.
2. GET /assets — list assets with status, unit, and criticality filters.
3. GET /assets/{asset_id} — retrieve an asset; return 404 if missing.
4. PUT /assets/{asset_id} — update an asset; explicitly reject any request body containing asset_id with HTTP 400.
5. DELETE /assets/{asset_id} — soft-delete an asset; deleted assets must not appear in GET results.

## VALIDATION
- asset_id must match `^[A-Z]{3}-\d{4}$`.
- criticality must be exactly High, Medium, or Low.
- Reject attempts to change asset_id, even if the original ID remains unchanged.
- Return HTTP 422 for invalid field values and HTTP 400 for asset_id modification attempts.
- Return structured JSON validation errors with `errors`, containing `field` and `reason`.
- Prevent duplicate asset IDs.
- Use Pydantic v2 validation and serialization methods.

## DATA
- Load `maintenance_assets.csv` containing 60 records at startup.
- Use the original CSV file without replacing or modifying it.
- Support dates in M/D/YYYY format, such as `5/5/2024`, converting them into valid date objects.
- Convert numeric CSV fields to appropriate Python types.
- Do not generate random replacement data if the CSV file is missing.
- Return a clear error if loading the CSV fails.
- Reset the in-memory test state between tests.

## IMPLEMENTATION
- Use a clean FastAPI application structure.
- Use FastAPI lifespan handling instead of deprecated startup events.
- Prefer Python standard library for reading CSV; if external dependencies are required, list them explicitly.
- Keep asset_id immutable.
- Ensure create, read, update, delete, and filtering behave consistently.

## TESTS
Use pytest and FastAPI TestClient.

Include at least one successful test and one failure test for every endpoint.

Additionally, test:
- Rejecting asset_id modification with HTTP 400.
- Invalid criticality returning HTTP 422.
- Duplicate asset_id rejection.
- Nonexistent asset returning HTTP 404.
- Soft-deleted assets no longer appearing in GET requests.
- Loading the original CSV successfully.

Do not modify tests merely to hide implementation failures.

## OUTPUT FORMAT
Provide one fenced code block per file, preceded by its filename.

Required files:
- main.py
- models.py
- test_api.py
- README.md

Include all required dependency installation commands in README.md.

Do not include prose between files.

## DEFINITION OF DONE
- `uvicorn main:app` starts successfully.
- `pytest -q` passes.
- All specified endpoints and validation rules are implemented.
- No TODOs, placeholders, or incomplete code.
- No deprecated Pydantic v1 serialization methods.
- No modifications to the original CSV dataset.