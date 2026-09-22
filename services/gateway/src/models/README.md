# Pydantic models

Request and response schemas for the gateway OpenAPI surface.

## Files

| File | Role |
|------|------|
| `__init__.py` | Re-exports common request/response models |
| `requests.py` | POST/PUT/PATCH bodies (agents, goals, plans, tasks) |
| `responses.py` | Response shapes (`AgentResponse`, `PlanResponse`, …) |

## Notes

- Validation failures become HTTP **422** before handlers run.
- `TaskUpdate` is defined in `requests.py` but not re-exported from `__init__`
  (routers import it directly).
- `TaskDeleteResponse` lives in `responses.py` and is imported by the tasks router.
