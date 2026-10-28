
# Lab 1.2 — Model Evaluation

## Model Information
- Requested model: openrouter/free
- Actual model: dots-studio/dots-3-note-preview:free
- Task: Generate a FastAPI CRUD API for asset maintenance records
- Dataset: maintenance_assets.csv (60 records)

## Evaluation Results

| Criterion | Result |
|---|---|
| All 5 endpoints generated | PASS |
| Validation rules enforced | PASS after fixes |
| Tests generated | PASS |
| Runs without manual fixes | FAIL |
| Initial test execution | ERROR during collection |
| Final pytest result | 10 passed, 0 failed, 2 warnings |
| Manual interventions | 6 recorded steps |

## Manual Interventions

1. Fixed incorrect regex `.match()` usage in models.py.
2. Added CSV date parsing in main.py.
3. Corrected invalid asset IDs used in test_api.py.
4. Fixed the FastAPI request validation error handler.
5. Added extra-field rejection to AssetUpdate.
6. Explicitly rejected asset_id changes with HTTP 400.

Note: Intervention #5 initially failed because the configuration
was placed in AssetBase instead of AssetUpdate. It was then
moved to the correct model.

## Remaining Issues
- Two Pydantic deprecation warnings involving `.dict()`.
- Only the 10 generated pytest tests were verified.
- Production readiness and broader edge cases were not tested.

## Autonomy Assessment
The model generated the required API structure but could not
produce a fully working implementation without human intervention.

The main weaknesses were runtime validation, consistency between
generated tests and validation rules, and HTTP error handling.

## Conclusion
The generated implementation passed all 10 tests after repairs,
but failed the requirement to run without manual fixes.
