# Architecture

```mermaid
flowchart TD
  UI[React + TypeScript UI] --> API[FastAPI REST API]
  API --> AUTH[Authentication]
  API --> SERVICES[Domain endpoints and services]
  SERVICES --> INTEL[Skill scoring / document analysis / job matching]
  SERVICES --> ORM[SQLAlchemy ORM]
  ORM --> DB[(SQLite database)]
  API --> DOC[PDF and DOCX extraction]
```

The frontend uses JSON REST endpoints under `/api`. FastAPI validates inputs and enforces authenticated user ownership. SQLAlchemy persists user data. Intelligence functions are kept in separate modules so their behavior can be tested independently.
