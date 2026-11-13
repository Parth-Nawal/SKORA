# Database overview

- `users`: account and profile identity.
- `skills`: user-owned skill profile entries.
- `activities`: dated practice/project/study records tied to a skill.
- `evidence`: work samples and other evidence; many-to-many relationship with skills through `evidence_skills`.
- `assessment_questions`: question bank, correct answers, and explanations.
- `assessment_attempts`: persisted scores and timestamps.

SQLite tables are created on startup for this MVP. Alembic migrations are a recommended next step before substantial schema evolution; the repository is structured to support adding them.
