# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

## Smarter Scheduling

PawPal+ now includes a smarter backend scheduling pipeline:

- recurring task handling: marking a `daily` or `weekly` task complete creates a new instance at `today + 1 day` or `today + 7 days` using `timedelta`.
- flexible sorting: tasks are sorted by priority and duration, and the scheduler offers a dedicated `sort_by_time()` helper.
- conflict detection: built-in `detect_conflicts()` warns when tasks overlap in time (no crash mode).

## Testing PawPal+

Run:

```bash
python -m pytest
```

Tests cover:
- Task behavior (completion, recurrence, adding tasks)
- scheduler behavior (sorting, conflict detection, filtering by pet/completion)
- daily plan generation and warning handling

Confidence Level: (4/5 stars) based on a passing pytest run with 5 tests and strong core coverage.


- Lets the user enter basic owner + pet info
- Lets the user add/edit tasks (duration + priority at minimum)
- Generates a daily schedule/plan based on constraints and priorities
- Displays the plan clearly (and ideally explain the reasoning)
- Includes tests for the most important scheduling behaviors

## Getting started
- h
### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip3 install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
