# PawPal+ System Architecture

## High-Level Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE (Streamlit)                    │
│  - Add pets, tasks, preferences                                      │
│  - Toggle: Standard vs. Predictive Mode                              │
│  - View daily schedule, warnings, confidence scores                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  INPUT VALIDATION    │
                    │  - Owner data        │
                    │  - Pet information   │
                    │  - Tasks (duration,  │
                    │    priority, freq)   │
                    └──────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
    ┌────────────────────────┐   ┌────────────────────────┐
    │  RETRIEVER MODULE      │   │  SCHEDULER LOGIC       │
    │                        │   │                        │
    │ Fetches task history:  │   │ Standard Mode:         │
    │ - Past start times     │   │ - Sort by priority     │
    │ - Due dates            │   │ - Schedule sequentially│
    │ - Completion records   │   │ - Start at 8:00 AM     │
    │                        │   │                        │
    │ Returns: List[Dict]    │   │ Predictive Mode:       │
    │ [{date, start_time,    │   │ - Use history (if any) │
    │   duration}...]        │   │ - Predict optimal time │
    │                        │   │ - Clamp to safe window │
    └────────────────────────┘   │ - Calculate confidence │
                │                 └────────────────────────┘
                │                          │
                │                          ▼
                │                ┌──────────────────────┐
                │                │ PREDICTION ENGINE    │
                │                │                      │
                │                │ For each task:       │
                │                │ 1. Check history len │
                │                │ 2. Calculate avg     │
                │                │    start time        │
                │                │ 3. Compute confidence│
                │                │ 4. Clamp to window   │
                │                │ 5. Return predicted  │
                │                │    time + confidence │
                │                └──────────────────────┘
                │                          │
                └──────────────┬───────────┘
                               │
                               ▼
                ┌─────────────────────────────────────┐
                │  EVALUATOR & CONFLICT DETECTION     │
                │                                     │
                │ - Check for overlapping tasks       │
                │ - Flag low-confidence predictions   │
                │ - Compute avg confidence for plan   │
                │ - Generate explanation text         │
                │ - Log all decisions (audit trail)   │
                └─────────────────────────────────────┘
                               │
                               ▼
                ┌─────────────────────────────────────┐
                │      DAILY PLAN (DailyPlan object)  │
                │                                     │
                │ - Date                              │
                │ - Scheduled tasks [                 │
                │     {task, start_time, end_time}    │
                │   ]                                 │
                │ - Total time (minutes)              │
                │ - Explanation text                  │
                │ - Warnings (conflicts)              │
                │ - Confidence score (0.0-1.0)       │
                │ - Record history for each task      │
                └─────────────────────────────────────┘
                               │
                               ▼
                ┌─────────────────────────────────────┐
                │      OUTPUT to USER (Streamlit)     │
                │                                     │
                │ - Display schedule in table         │
                │ - Show confidence scores            │
                │ - Highlight conflicts as warnings   │
                │ - Provide explanation of reasoning  │
                │ - Log entries for audit trail       │
                └─────────────────────────────────────┘
                               │
                               ▼
                ┌─────────────────────────────────────┐
                │    USER DECISION & FEEDBACK         │
                │                                     │
                │ - Accept schedule → record history  │
                │ - Toggle mode → regenerate          │
                │ - Override manually → update state  │
                └─────────────────────────────────────┘
```

---

## Component Details

### 1. **Retriever Module** (`pawpal_system.py: Task.history`)
**Purpose**: Fetch historical scheduling data for a task.

**Data Retrieved**:
- List of past (date, start_time, duration) tuples
- Used to compute average start times and confidence

**Key Methods**:
- `Task.record_history(date, start_time)` — Save a schedule entry
- Automatic append to `task.history` list during `generate_predictive_plan()`

**Example Output**:
```python
task.history = [
    {"date": 2026-04-20, "start_time": 08:15, "duration": 20},
    {"date": 2026-04-21, "start_time": 08:30, "duration": 20},
    {"date": 2026-04-22, "start_time": 08:00, "duration": 20},
]
```

---

### 2. **Logic Module** (`pawpal_system.py: Scheduler`)
**Purpose**: Decide which tasks to schedule and when (standard or predictive mode).

**Standard Mode** (`generate_daily_plan`):
1. Filter tasks due today and incomplete
2. Sort by priority (high first) then duration (short first)
3. Schedule sequentially starting at 8 AM
4. Detect conflicts
5. Return plan with warnings

**Predictive Mode** (`generate_predictive_plan`):
1. Filter tasks due today and incomplete
2. For each task, call prediction engine
3. Sort tasks by predicted start time + priority
4. Respect time windows (no scheduling before 8 AM or after 6 PM)
5. Record history for next prediction
6. Detect conflicts
7. Return plan with confidence scores

**Key Methods**:
- `Scheduler.sort_by_time(tasks)` — Sort by duration
- `Scheduler.predict_task_start_time(task, plan_date)` — AI prediction
- `Scheduler.generate_daily_plan(plan_date)` — Standard mode
- `Scheduler.generate_predictive_plan(plan_date)` — AI mode

---

### 3. **Prediction Engine** (`pawpal_system.py: predict_task_start_time`)
**Purpose**: Use historical data to forecast the best start time for a task.

**Algorithm**:
1. Determine preferred time window (e.g., "morning" → 8 AM–10 AM)
2. If history exists:
   - Average the past start times
   - Clamp average to preferred window
   - Confidence = 0.25 + (0.1 × number_of_past_instances), capped at 0.75
3. If no history:
   - Use default time for preference (e.g., 9 AM for morning)
   - Confidence = 0.35

**Error Handling**:
- If calculation fails, log exception and return default time
- Never crashes; always returns a valid fallback

**Confidence Scoring**:
| History | Confidence | Reasoning |
|---------|-----------|-----------|
| None | 0.35 | Low; using default |
| 1-2 instances | 0.45–0.65 | Medium; small sample |
| 3+ instances | 0.65–0.75 | High; reliable pattern |

---

### 4. **Evaluator & Conflict Detection** (`pawpal_system.py: Scheduler.detect_conflicts`)
**Purpose**: Check for scheduling conflicts and validate the plan before presenting to user.

**Conflict Detection Algorithm**:
1. For each pair of tasks in the plan:
   - Convert start/end times to minutes since midnight
   - Check if time ranges overlap: `s1 < e2 AND s2 < e1`
2. If overlap found, add warning: `"Conflict: Task A overlaps Task B"`

**Validation Checks**:
- No task starts before available hours (8 AM default)
- No task ends after closing time (6 PM default)
- All predicted confidence scores are between 0 and 1

**Output**:
- List of warning strings (empty if no conflicts)
- Average confidence score for the plan

---

### 5. **Logging & Audit Trail** (Python `logging` module)
**Purpose**: Create an auditable record of all AI decisions and predictions.

**Logged Events**:
- ✓ Task history recorded: `"Recorded history for task 'Walk' at 08:45"`
- ✓ Prediction made: `"Predicted start for 'Feed' at 08:30 (confidence=0.65)"`
- ✓ Conflict detected: `"Conflict: 'Walk' overlaps 'Play'"`
- ✓ Prediction failed: `"Prediction failed for task 'Playtime'; falling back to default"`

**Log Format**:
```
2026-04-27 10:15:22 INFO - Recorded history for task 'Walk' at 08:45
2026-04-27 10:15:23 INFO - Predicted start for 'Feed' at 08:30 (confidence=0.65)
2026-04-27 10:15:24 INFO - Detected conflict: 'Walk' overlaps 'Play'
```

**Access Logs**:
```bash
# Enable debug logging
streamlit run app.py --logger.level=debug

# Search logs for audit trail
grep "Predicted\|Recorded\|Conflict" *.log
```

---

## Data Schema

### Task Object (with AI extensions)
```python
@dataclass
class Task:
    description: str        # "Walk the dog"
    category: str          # "exercise"
    time: int              # 20 (minutes)
    priority: int          # 1-5 (1=low, 5=high)
    frequency: str         # "daily", "weekly", "once"
    preferred_time: str    # "morning", "afternoon", "evening"
    due_date: date         # Today's date
    completion_status: bool
    history: List[Dict]            # [{"date": ..., "start_time": ..., "duration": ...}]
    predicted_confidence: float     # 0.0-1.0
```

### DailyPlan Object (with confidence)
```python
@dataclass
class DailyPlan:
    date: date              # Today
    scheduled_tasks: List[Dict]  # [{"task": Task, "start_time": time, "end_time": time}]
    total_time: int         # Sum of task durations
    explanation: str        # "Scheduled 3 tasks in priority order..."
    warnings: List[str]     # ["Conflict: Walk overlaps Play"]
    confidence_score: float # 0.0-1.0 (avg of task confidences)
```

---

## User Interaction Flow

```
1. USER OPENS APP
   └─> Streamlit loads
   └─> Initialize Owner + Scheduler in session_state

2. USER ADDS PETS & TASKS
   └─> Task added to pet.tasks list
   └─> UI shows task in "Current Tasks" section

3. USER CLICKS "GENERATE SCHEDULE"
   │
   └─> MODE SELECTION:
       ├─ Predictive Mode? → Call scheduler.generate_predictive_plan()
       │  └─> Retrieve history → Predict times → Calculate confidence → Detect conflicts
       │
       └─ Standard Mode? → Call scheduler.generate_daily_plan()
          └─> Sort by priority → Schedule sequentially → Detect conflicts

4. SCHEDULER RETURNS PLAN
   └─> DailyPlan with tasks, times, confidence, warnings, explanation

5. UI DISPLAYS RESULTS
   ├─ Table: Task | Start | End | Confidence | Duration
   ├─ Warnings: "Conflict: X overlaps Y"
   ├─ Explanation: "Predicted optimal daily schedule using historical start times..."
   └─ Confidence Score: 0.65 (average)

6. USER REVIEWS & DECIDES
   ├─ Accept → Plan confirmed, history recorded
   ├─ Toggle Mode → Regenerate with different algorithm
   └─ Override → Manually edit schedule (future feature)
```

---

## AI Capabilities Map

| AI Requirement | How PawPal+ Fulfills It | Implementation |
|---|---|---|
| **Retrieve Information** | Fetch task history from past schedules | `Task.history` list + retriever logic |
| **Plan & Complete Step-by-Step Task** | Generate multi-task daily schedule with reasoning | `generate_predictive_plan()` + conflict detection |
| **Help Debug/Classify/Explain** | Show confidence scores + logging + explanations | Confidence scoring + audit trail |
| **Fully Integrated** | AI predictions actively change scheduling behavior | Predictive mode switches algorithm; history affects output |
| **Runs Correctly & Reproducibly** | 7 passing tests; deterministic algorithm | pytest suite + version-controlled code |
| **Includes Logging** | Full audit trail of predictions + decisions | Structured Python `logging` module |
| **Clear Setup Steps** | README with installation + running instructions | Complete setup guide |

---

## References

- **Architecture Pattern**: Retriever → Logic → Evaluator (RAG-inspired)
- **Responsible AI**: Confidence scoring + user control + logging (see `ai_guardrails.md`)
- **Testing Strategy**: Unit tests for core behaviors + integration tests for full flow
