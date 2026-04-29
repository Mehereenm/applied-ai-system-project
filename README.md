# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## Smarter Scheduling

PawPal+ now includes a smarter backend scheduling pipeline:

- Recurring task handling: Marking a daily or weekly task complete creates a new instance at, today + 1 day or today + 7 days using timedelta.
- Flexible sorting: tasks are sorted by priority and duration.
- Predictive scheduling: the app uses task history and preferred time windows to forecast better start times for recurring care tasks.
- Conflict detection: built-in detect_conflicts() warns when tasks overlap in time.

## Testing PawPal+

Run:

```bash
cd ai110-pawpal-starter
```

### Step 2: Create and activate virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows
```

### Step 3: Install dependencies
```bash
pip3 install -r requirements.txt
```

**Requirements file** (`requirements.txt`):
```
streamlit>=1.30
pytest>=7.0
```

### Step 4: Run tests (optional, but recommended)
```bash
python -m pytest tests/test_pawpal.py -v
```


### Step 5: Launch the Streamlit app
```bash
streamlit run app.py
```

The app will open browser at `http://localhost:8501`.

---

## Sample Interactions

### Example 1: First-Time User (No History)

**Scenario**: New user adds pets and tasks. Confidence is low because no history exists.

**Setup**:
```
Owner: Alex
Pet 1: Buddy (Dog, age 3)
Task 1: "Morning Walk" - 20 min, priority 5, morning
Task 2: "Breakfast" - 10 min, priority 4, morning
```

**Predictive Plan Output**:
```
Daily Plan for 2026-04-27:

Table:
┌─────────────────┬───────┬────────┬────────┬─────────────────┬──────────┐
│ Task            │ Pet   │ Start  │ End    │ Confidence      │ Duration │
├─────────────────┼───────┼────────┼────────┼─────────────────┼──────────┤
│ Morning Walk    │ Buddy │ 09:00  │ 09:20  │ 0.35 (default)  │ 20 min   │
│ Breakfast       │ Buddy │ 09:20  │ 09:30  │ 0.35 (default)  │ 10 min   │
└─────────────────┴───────┴────────┴────────┴─────────────────┴──────────┘

Explanation:
"Predictes optimal daily schedule using historical start times and preferred 
time windows. Confidence: 0.35."

(No history yet, so both tasks default to preferred morning window.)
```

**Users**: Accept schedule. History is recorded.

**Logs**:
```
Records history for task 'Morning Walk' at 09:00
Records history for task 'Breakfast' at 09:20
```

---

### Example 2: Recurring User with Pattern (High Confidence)

**Scenario**: Same user runs predictive scheduling 3 days in a row. The AI now has history and improves confidence.

**History for "Morning Walk"**:
```
Day 1: 09:00
Day 2: 08:45
Day 3: 08:50
Average: 08:51, Confidence: 0.65 (3 instances)
```

**Predictive Plan Output**:
```
Daily Plan for 2026-04-30:

Table:
┌─────────────────┬───────┬────────┬────────┬──────────────────┬──────────┐
│ Task            │ Pet   │ Start  │ End    │ Confidence       │ Duration │
├─────────────────┼───────┼────────┼────────┼──────────────────┼──────────┤
│ Morning Walk    │ Buddy │ 08:51  │ 09:11  │ 0.65 (history)   │ 20 min   │
│ Breakfast       │ Buddy │ 09:11  │ 09:21  │ 0.55 (2 samples) │ 10 min   │
└─────────────────┴───────┴────────┴────────┴──────────────────┴──────────┘

Explanation:
"Predicts best daily schedule using historical start times and preferred 
time windows. Confidence: 0.60."

(System is now more confident; walk at 08:51 based on average of 3 past runs.)
```

---

### Example 3: Conflict Detection & Warning

**Scenario**: User adds overlapping tasks.

**Setup**:
```
Task 1: "Morning Walk" - 20 min, starts 08:00
Task 2: "Grooming" - 25 min, starts 08:15
Task 3: "Breakfast" - 10 min, starts 08:25
```

**Plan Output**:
```
⚠️ WARNINGS:
  Conflict: 'Morning Walk' (exercise) overlaps with 'Grooming' (grooming).
  Conflict: 'Grooming' (grooming) overlaps with 'Breakfast' (feeding).

Table:
┌──────────────────┬────────┬────────┬────────────────────────┐
│ Task             │ Start  │ End    │ Status                 │
├──────────────────┼────────┼────────┼────────────────────────┤
│ Morning Walk     │ 08:00  │ 08:20  │ ✓ Scheduled           │
│ Grooming         │ 08:20  │ 08:45  │ ✓ Scheduled (adjusted) │
│ Breakfast        │ 08:45  │ 08:55  │ ✓ Scheduled (adjusted) │
└──────────────────┴────────┴────────┴────────────────────────┘
```

**Users**: Adjust task durations or priorities, then regenerate.

---

## Design Decisions & Trade-offs

### Decision 1: Confidence Capping at 0.75
- To prevent overconfidence. Even with good historical data, external factors (pet illness, schedule changes) can disrupt patterns.
**Trade-off**: Conservative; users might expect higher confidence with extensive history.

### Decision 2: Time Window Clamping
- To prevent scheduling tasks at unreasonable hours (midnight walk? Not helpful).
**Implementation**: 
- Morning: 8 AM–10 AM (default 9 AM)
- Afternoon: 12 PM–3 PM (default 1 PM)
- Evening: 5 PM–7 PM (default 6 PM)

**Trade-off**: Less flexibility, but safer and more practical.

### Decision 3: History Recording During Plan Generation
- To capture actual usage patterns. When a schedule is accepted, times are recorded.
**Trade-off**: History reflects only "accepted" schedules, not "attempted" ones.
**Benefit**: More realistic patterns; reflects what actually worked.

### What Worked 
- Confidence scoring motivates improvements
- History recording creates predictable patterns
- Fallback behavior (no crashes) builds reliability
- Logging provides transparency for debugging

### What Didn't Work (Lessons Learned) 
1. **Initial typing issues** (Python 3.9 | vs Optional): Fixed by using Optional[Type] syntax
2. **Duplicate conflict detection method**: Removed redundant method to keep code DRY
3. **Over-eager confidence**: Initially wanted higher confidence scores; refactored to be conservative

# Single Owner & Pet:
Doesn’t handle multiple pets or coordinating tasks between pets
Simpler for now, but future updates could add multi-pet support.

# No External Factors:
Ignores weather, owner’s calendar, or pet health events.
Predictions are based only on past task times.

# Data Privacy
- All data is local. No cloud sharing.

# Clear Confidence Scores
- Confidence shows how much history the prediction is based on, not accuracy.

---

## Reflection: What I Learned

# Not Enough Data
- If there are only 2–3 past entries, predictions aren’t very reliable.
- Confidence scores are capped at 0.75 to prevent false trust.
- The system expects owners to follow the same schedule every day.
- Life changes (sickness, weather, pet health) can make predictions less accurate.
- Users can see logs to notice when predictions are off.

# Overall Lesson:
 AI is great for calculations and formatting, but design decisions (like which data to trust) require human judgment.
---

## Running the Project

### Quick Start
```bash
# Setup (one-time)
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt

# Run tests
python -m pytest tests/test_pawpal.py -v

# Launch app
streamlit run app.py
```

### Using the App

1. **Add a Pet**: Enter name, species, age
2. **Add Tasks**: For each pet, create tasks with duration, priority, category
3. **Generate Schedule**:
   - Check "Use predictive scheduling" for AI mode (recommended after 2–3 runs)
   - Click "Generate Schedule" to see the daily plan
4. **Review Results**:
   - Table shows tasks, start times, confidence scores
   - Warnings highlight any conflicts
   - Explanation text explains the reasoning

Video link: https://www.dropbox.com/scl/fi/52i9glrk8e3bq840e3hk7/Codepath_recording.mp4?rlkey=l9n26z18p5u44igw528sytc90&st=ig198zvy&dl=0