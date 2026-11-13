# SKORA Intelligence Algorithms

## Skill health
The backend combines available signals with configurable weights: assessment average (0.40), activity recency (0.25), practice consistency (0.20), and evidence count score (0.15). When a signal is missing, weights are renormalized over available signals. If no signal exists, the health score is `null` and the status is `Insufficient Data`.

## Practice recency
`recency = 100 * exp(-days_since_last_practice / 30)`

This is an activity-freshness heuristic, not a validated model of memory retention.

## Consistency
The current MVP uses up to 20 points per recorded activity in the last 30 days, capped at 100. This rewards regular logging but can be improved by measuring active days rather than number of entries.

## Evidence
Each linked evidence item contributes 35 points, capped at 100. Evidence count does not mean external verification or proof of mastery.

## Job matching
A curated alias dictionary detects skills in a job description. Coverage is the percentage of detected skills found by name in the user's profile. It is not a hiring probability and currently does not deeply weight skill health or evidence.

## Limitations and next improvements
- Introduce skill-specific decay constants and calibration against user assessment history.
- Add activity-day consistency, not just event count.
- Expand alias taxonomy and negative-context handling.
- Add assessment topic-level mapping.
- Add explicit resume-to-evidence claim comparison in a future iteration.
