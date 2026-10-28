
# Lab 1.2 — Laguna Evaluation

## Model Information
- Requested model: poolside/laguna-s-2.1:free
- Actual model: poolside/laguna-s-2.1:free
- Dataset: maintenance_assets.csv (60 records)

## Test Results
- Initial pytest: Collection error (pandas missing)
- After installing pandas: 16/16 passed
- Independent asset_id check: Failed (HTTP 200 instead of 400)
- After manual code repair: 16/16 original tests passed
- Independent asset_id retest: Passed (HTTP 400)
- Remaining warnings: 2

## Manual Interventions
1. Installed pandas in the project environment.
2. Replaced update_asset implementation to reject asset_id changes and preserve validation handling.

## Observations
- Generated all five CRUD endpoints.
- Generated 16 pytest tests.
- Used pandas for CSV data loading.
- Missed explicit rejection of asset_id changes.
- Used deprecated FastAPI startup event handling.

## Conclusion
Laguna passed all 16 generated tests after installing
the missing dependency, but an independent test exposed
an asset_id validation issue.

After manual repair, the original 16 tests and the
independent asset_id check passed.

## Comparison Limitations
- The three models generated different test suites.
- Results are not directly comparable by test count alone.
- Only three free models were evaluated instead of the
  four specified model families.
