# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The PawPal+ system is built around five main parts: Pet, Task, Owner, Scheduler, and DailyPlan. Together, they help organize and plan pet care.

Pet: Stores basic info about the pet (name, type, age, special needs) and lets you view or update it.

Task: Represents a care activity (like feeding or walking). It includes details like how long it takes, how important it is, how often it happens, and when it should be done.

Owner: Holds information about the owner’s schedule and preferences, such as how much time they have each day and when they prefer to start or end tasks.

Scheduler: The “brain” of the system. It takes the pet, owner, and tasks, applies any rules or limits, and creates a daily plan.

DailyPlan: The final schedule for the day. It lists tasks with their times, total time needed, and a short explanation of the plan.

Relationships: Scheduler aggregates Pet, Owner, and a list of Tasks; it generates a DailyPlan. Tasks are associated with the Pet, and the Owner provides constraints for the Scheduler.

The Scheduler uses the Pet, Owner, and Tasks to create a DailyPlan. Tasks are for the pet, and the owner’s availability helps decide when they can be done.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

**c. Core User Actions**

Based on the scenario in README.md, PawPal+ is designed to help busy pet owners plan and track pet care tasks by generating daily schedules considering constraints like time availability, task priorities, and owner preferences.

The three core actions a user should be able to perform are:

1. Add a pet: Enter basic information about the owner and their pet, such as pet name, type, age, and any special needs. 

2. Add/edit tasks: Create or modify pet care tasks, including details like task type (e.g., walk, feeding, medication), duration, priority level, and any specific preferences or constraints. For example, scheduling a daily walk with a set duration and high priority.

3. View today's tasks: Generate and display a daily schedule or plan of tasks based on the entered information, constraints, and priorities. 

4. Generate a schedule

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities/Tradeoffs**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?
- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

This keeps the system simple and fast, which is good for an early version (MVP). Instead of automatically solving conflicts, it lets the user see the issue and adjust task times or priorities themselves.

- Confidence shows how much history the prediction is based on, not accuracy.
- Doesn’t handle multiple pets or coordinating tasks between pets
- Ignores weather, owner’s calendar, or pet health events.
---

## 3. AI Collaboration

**a. How you used AI**

- Used Copilot to suggest iteration patterns (e.g., sorted() key functions, dataclass syntax, simple conflict detection and recurrence logic).
- Used copilot to generate system_architecture.mg, for visual of system diagram
- Prompts that worked best included: "implement a scheduler method to sort tasks by duration" and "show overlap detection code for task start/end time." 

**b. Judgment and verification**

- One AI suggestion rejected: Copilot suggested a full backtracking interval scheduling conflict solver; I chose to keep a simpler, readable pairwise overlap warning strategy to avoid over-engineering.
- Verification used direct unit tests (test_sort_by_time_correctness, test_recurrence_logic_daily, test_conflict_detection_duplicate_time) and terminal outputs from main.py.

**c. Lead architect lesson**

- Separating into phases (design, implementation, UI) kept focus and reduced scope creep; each phase had its own chat session.
- Being the lead architect means you keep final control, prune suggestions, and enforce clear API boundaries through code and tests.

---

## 4. Testing and Verification

### Automated Testing (7/7 Tests Passing)

The system's core behaviors are verified through unit tests covering:

**Standard Scheduling Tests**:
- test_task_completion: Verifies task completion status changes and recurrence generation
- test_task_addition: Confirms tasks are properly added to pets
- test_sort_by_time_correctness: Validates sorting by duration
- test_recurrence_logic_daily: Checks next-day recurrence calculation
- test_conflict_detection_duplicate_time: Detects overlapping task times

**Predictive AI Tests**:
- test_predictive_plan_uses_history: Ensures historical data is used for predictions
- test_generate_predictive_plan_without_history: Verifies fallback behavior when no history exists

**Run tests anytime:**
```bash
python -m pytest tests/test_pawpal.py -v
```

**Result**: All 7 tests pass consistently, covering happy path, edge cases, and error recovery.

### 2. Confidence Scoring (Measures Prediction Certainty)

Each predicted task time includes a confidence score (0.0–1.0) that reflects the reliability of the prediction:

**Examples**:
```
Day 1 (No History):
  - Morning Walk prediction: 09:00 AM
  - Confidence: 0.35 (default; no pattern yet)

Day 2-4 (Recurring):
  - Day 2 actual: 08:45 AM → recorded
  - Day 3 actual: 08:30 AM → recorded
  - Day 4 actual: 08:50 AM → recorded
  - Average: 08:41 AM
  - Confidence: 0.65 (3 samples; moderate certainty)

Day 7 (After 5 executions):
  - Predicted: 08:42 AM (average of 5 past times)
  - Confidence: 0.75 (capped; strong pattern)
```


**Log Events Captured**:
```
[Prediction Event]
2026-04-01 10:15:22 INFO - Recorded history for task 'Walk' at 08:45
2026-04-01 10:15:23 INFO - Predicted start for 'Feed' at 08:30 (confidence=0.65)

[Conflict Detection]
2026-04-01 10:15:24 INFO - Detected conflict: 'Walk' overlaps 'Play'

[Error Handling]
2026-04-01 10:15:25 ERROR - Prediction failed for 'Playtime'; falling back to 09:00


**Error Recovery**:
- If prediction logic fails → Log the exception + cause
- Fallback to default time (e.g., 9 AM for "morning")
- Return confidence = 0.0 to signal fallback
- Always return a valid schedule
```

###4. Validation & Quality Metrics

**Test Results Summary**:
- **Pass Rate**: 7 out of 7 tests passed (100%)
- **Coverage**: Core logic + AI predictions + edge cases
- **Failure Modes**: All caught (no history, conflicts, prediction errors)

**Sample Accuracy Analysis**:
```
Task: "Morning Walk"
Past 5 schedules: 08:50, 08:45, 08:55, 08:40, 08:48
Predicted: 08:48 (average)
Actual baseline: 08:50
Error: 2 minutes (within tolerance)
Confidence: 0.70 
```

---

## 5. Reflection

**a. What went well**

- I am most satisfied with how the predictive scheduling feature was integrated into the existing system without breaking the original schedule generation flow.


**b. What you would improve**

- **Seasonal Models**: Add awareness of daylight changes, weather, and pet age so the system can schedule differently in winter versus summer.
- **Multi-Pet Coordination**: Support grouping tasks for multiple pets, such as walking two dogs together or sharing a single grooming slot.
- **Anomaly Filtering**: Include a lightweight filter to ignore rare outlier times that should not affect the average prediction.
- **API Integration**: Use external activity or health data, such as vet appointments or fitness tracker summaries, to make predictions more context-aware.

**c. Key takeaway**

- The most important lesson was that a useful AI system does not need to be complex; it needs to be transparent, testable, and aligned with the user’s real workflow.
- I also learned that human judgment is still critical when choosing what to automate and when to leave control with the user.



