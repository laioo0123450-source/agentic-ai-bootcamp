
# Lab 1.2 — Nemotron Evaluation

## Model
- Requested: nvidia/nemotron-3-ultra-550b-a55b:free
- Actual: nvidia/nemotron-3-ultra-550b-a55b:free
- Dataset: maintenance_assets.csv (60 records)

## Test Results
- Original generated tests: 12/12 passed on first run
- Independent asset_id test: Failed (HTTP 200 instead of 400)
- Final tests: 13/13 passed
- Remaining warnings: 4
- Manual repair steps: 2

## Manual Repairs
1. Modified update_asset to reject asset_id changes with HTTP 400.
2. Added handling for Pydantic ValidationError to preserve HTTP 422 for invalid data.

## Observations
- Generated all five CRUD endpoints.
- Used FastAPI and Pydantic models.
- Generated 12 pytest tests.
- Included structured validation errors.
- Did not originally test asset_id immutability.
- Included deprecated FastAPI/Pydantic patterns.

## Conclusion
Nemotron passed its original tests without code repairs,
but missed one requirement detected by an independent test.
After two manual repair steps, all 13 tests passed.

## Comparison Limitations
- Dots3 and Nemotron generated different test suites.
- A shared independent test suite is still needed.
- Nemotron is an additional NVIDIA model, not a direct
  substitute for GPT, Claude, LLaMA, or Mistral.
