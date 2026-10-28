# Lab 1.2 — CRUD API Model Comparison

## 1. Objective

Evaluate the ability of multiple free LLMs to generate a runnable FastAPI CRUD application from the same prompt, measure their first-run success, document manual interventions, and improve the original prompt.

## 2. Experimental Setup

- Stack: Python 3.12, FastAPI, Pydantic v2, pytest
- Dataset: maintenance_assets.csv (60 records)
- Prompt: CRUD API Builder v1.0
- Provider: OpenRouter
- Evaluation scope: Three free models

## 3. Models Evaluated

| Model | Original Tests | Final Result | Interventions |
|---|---|---|---|
| Dots3 Note Preview | Failed initial execution | 10/10 passed | 6 documented repair steps |
| NVIDIA Nemotron 3 Ultra | 12/12 passed | 13/13 passed | 2 code repairs |
| Poolside Laguna S 2.1 | Dependency missing initially | 16/16 + independent check passed | 1 code repair + pandas installation |

## 4. Key Findings

### Dots3
Generated the required CRUD structure but required several repairs involving validation, CSV date parsing, test consistency, and HTTP error handling.

### Nemotron
Passed its 12 generated tests without code repairs. An independent test revealed that asset_id modification attempts were silently ignored, requiring two repair steps.

### Laguna
Generated 16 passing tests after installing pandas. An independent check exposed the same asset_id issue, which was corrected manually.

## 5. Cross-Model Observations

- All three models generated code for the required five CRUD endpoints.
- Generated test counts did not guarantee complete requirement coverage.
- Explicit asset_id immutability enforcement was a recurring weakness.
- Environment dependencies affected first-run reproducibility.
- Independent evaluation revealed issues that self-generated tests missed.

## 6. Prompt Improvement

The prompt was improved from v1.0 to v1.1 to clarify:
- HTTP 400 for asset_id modification attempts.
- HTTP 422 for invalid field values.
- CSV date formats and preservation of original data.
- Required dependencies and startup behavior.
- Independent negative test cases.
- Avoidance of deprecated APIs.

## 7. Limitations

- Only three free models were evaluated.
- The requested GPT, Claude, LLaMA, and Mistral model families were not directly compared.
- The three models generated different test suites.
- A complete shared benchmark and production-level evaluation were not performed.
- Prompt v1.1 was designed but not rerun against the models.

## 8. Conclusion

NVIDIA Nemotron 3 Ultra showed the strongest first-run code execution performance in this experiment, while Poolside Laguna S 2.1 required only an additional dependency before passing its generated tests. Dots3 required the most manual repairs.

The experiment demonstrates that AI-generated code can accelerate development, but successful execution of self-generated tests does not guarantee complete compliance with requirements. Precise prompts and independent validation remain essential.
