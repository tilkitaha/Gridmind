> Historical product proposal. Superseded for thesis scope on 21 September 2026. Not evidence of implemented research capabilities.

# Architecture — GridMind

## Design goals

- Small, understandable core.
- Domain logic independent from FastAPI.
- Provider/model integrations behind adapters.
- Safe-by-default approval boundaries for actions.
- Testable without external API keys.

## Current runtime

```text
HTTP Request
   │
   ▼
FastAPI route
   │
   ▼
Domain function (`src/app/core.py`)
   │
   ▼
Deterministic MVP result
```

## Target runtime

```text
Web / Mobile / Device
        │
        ▼
API Gateway + Auth
        │
        ▼
Application Services
   ┌────┼────────┐
   ▼    ▼        ▼
Agents Domain  Workflow Engine
   │    │        │
   └────┼────────┘
        ▼
Model / Data / Tool Adapters
        │
  ┌─────┼─────────────┐
  ▼     ▼             ▼
LLM   PostgreSQL   External APIs
```

## Engineering rules

1. No secrets in source control.
2. No irreversible external action without an explicit permission boundary.
3. Domain logic stays testable offline.
4. AI outputs are treated as untrusted data and validated.
5. Every material action should be auditable in production.
