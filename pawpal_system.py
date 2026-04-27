from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, time, datetime, timedelta
import logging
import statistics

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(name)s:%(message)s")

@dataclass
class Task:
    description: str
    category: str
    time: int  # in minutes
    priority: int  # 1-5, higher is more important
    frequency: str  # e.g., "daily", "weekly"
    preferred_time: str  # e.g., "morning", "evening"
    due_date: Optional[date] = None
    completion_status: bool = False
    history: List[Dict[str, Any]] = field(default_factory=list)
    predicted_confidence: float = 0.0

    def is_due(self, check_date: date) -> bool:
        """Check if the task is due on the given date."""
        # Simple implementation: assume daily tasks are always due
        # For more complex, check frequency against date
        if self.frequency == "daily":
            return True
        # Add logic for other frequencies if needed
        return False

    def get_time(self) -> int:
        """Return the time required for the task in minutes."""
        return self.time

    def set_priority(self, priority: int):
        """Set the priority level of the task (1-5)."""
        self.priority = priority

    def record_history(self, scheduled_date: date, start_time: time):
        """Save a historical schedule entry for this task."""
        self.history.append({
            "date": scheduled_date,
            "start_time": start_time,
            "duration": self.time,
        })
        logger.info("Recorded history for task '%s' at %s", self.description, start_time)

    def mark_complete(self) -> "Task | None":
        """Mark the task as completed and create the next recurring instance if needed."""
        self.completion_status = True

        if self.frequency not in {"daily", "weekly"}:
            return None

        current_due = self.due_date if self.due_date is not None else date.today()
        if self.frequency == "daily":
            next_due = current_due + timedelta(days=1)
        else:
            next_due = current_due + timedelta(weeks=1)

        return Task(
            description=self.description,
            category=self.category,
            time=self.time,
            priority=self.priority,
            frequency=self.frequency,
            preferred_time=self.preferred_time,
            due_date=next_due,
            completion_status=False,
            history=self.history.copy(),
        )

@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: List[str]
    tasks: List[Task] = field(default_factory=list)

    def get_info(self) -> Dict[str, Any]:
        """Return a dictionary containing pet details and task descriptions."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "special_needs": self.special_needs,
            "tasks": [task.description for task in self.tasks]
        }

    def update_info(self, new_info: Dict[str, Any]):
        """Update pet attributes with the provided dictionary."""
        for key, value in new_info.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def add_task(self, task: Task):
        """Add a task to the pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task):
        """Remove a task from the pet's task list if it exists."""
        if task in self.tasks:
            self.tasks.remove(task)

@dataclass
class Owner:
    name: str
    available_hours_per_day: int
    preferred_start_time: str
    preferred_end_time: str
    preferences: Dict[str, Any]
    pets: List[Pet] = field(default_factory=list)

    def get_available_time(self) -> int:
        """Return the owner's available hours per day."""
        return self.available_hours_per_day

    def update_preferences(self, new_prefs: Dict[str, Any]):
        """Update the owner's preferences with new values."""
        self.preferences.update(new_prefs)

    def add_pet(self, pet: Pet):
        """Add a pet to the owner's pet list."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return a flattened list of all tasks from all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

@dataclass
class Scheduler:
    owner: Owner
    constraints: Dict[str, Any]

    def add_task(self, task: Task, pet: Pet):
        """Add a task to the specified pet if owned by the owner."""
        if pet in self.owner.pets:
            pet.add_task(task)

    def remove_task(self, task: Task, pet: Pet):
        """Remove a task from the specified pet if owned by the owner."""
        if pet in self.owner.pets:
            pet.remove_task(task)

    def mark_task_complete(self, task: Task, pet: Pet):
        """Mark a task complete for a given pet and add its next recurring instance if needed."""
        if pet not in self.owner.pets:
            raise ValueError("Pet not found for owner")

        if task not in pet.tasks:
            raise ValueError("Task not found for pet")

        next_task = task.mark_complete()
        if next_task is not None:
            # Enqueue next recurrence instance
            pet.add_task(next_task)
        return next_task

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Return tasks sorted by ascending duration (minutes)."""
        return sorted(tasks, key=lambda t: t.time)

    def preferred_time_window(self, preferred_time: str) -> Tuple[int, int]:
        """Return a safe window in minutes for preferred times of day."""
        pref = preferred_time.lower()
        if pref == "morning":
            return 8 * 60, 10 * 60
        if pref == "afternoon":
            return 12 * 60, 15 * 60
        if pref == "evening":
            return 17 * 60, 19 * 60
        return 8 * 60, 18 * 60

    def default_start_for_preference(self, preferred_time: str) -> time:
        """Return a default safe start time for a preferred time window."""
        pref = preferred_time.lower()
        if pref == "morning":
            return time(9, 0)
        if pref == "afternoon":
            return time(13, 0)
        if pref == "evening":
            return time(18, 0)
        return time(8, 0)

    def clamp_minutes(self, candidate: int, window: Tuple[int, int]) -> int:
        """Clamp a minute value to a preferred time window."""
        start, end = window
        return max(start, min(candidate, end))

    def predict_task_start_time(self, task: Task, plan_date: date) -> time:
        """Predict the best start time for a task using past schedule history."""
        try:
            window = self.preferred_time_window(task.preferred_time)
            if task.history:
                past_minutes = [entry["start_time"].hour * 60 + entry["start_time"].minute for entry in task.history]
                average_minutes = int(statistics.mean(past_minutes))
                predicted_minutes = self.clamp_minutes(average_minutes, window)
                confidence = min(0.75, 0.25 + 0.1 * len(past_minutes))
            else:
                predicted_minutes = self.default_start_for_preference(task.preferred_time).hour * 60
                confidence = 0.35

            task.predicted_confidence = confidence
            predicted_time = time(predicted_minutes // 60, predicted_minutes % 60)
            logger.info("Predicted start for '%s' at %s (confidence=%.2f)", task.description, predicted_time, confidence)
            return predicted_time
        except Exception as exc:
            logger.exception("Prediction failed for task '%s'", task.description)
            return self.default_start_for_preference(task.preferred_time)

    def detect_conflicts(self, plan: 'DailyPlan') -> List[str]:
        """Detect conflicts where tasks overlap in scheduled time windows."""
        warnings = []
        entries = plan.scheduled_tasks

        def minutes_of(t: time) -> int:
            return t.hour * 60 + t.minute

        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                t1 = entries[i]
                t2 = entries[j]
                s1, e1 = minutes_of(t1['start_time']), minutes_of(t1['end_time'])
                s2, e2 = minutes_of(t2['start_time']), minutes_of(t2['end_time'])

                if s1 < e2 and s2 < e1:
                    warnings.append(
                        f"Conflict: '{t1['task'].description}' ({t1['task'].category}) overlaps "
                        f"with '{t2['task'].description}' ({t2['task'].category})."
                    )

        return warnings

    def generate_daily_plan(self, plan_date: date) -> 'DailyPlan':
        """Generate a daily plan by scheduling due tasks in priority order."""
        tasks = self.owner.get_all_tasks()
        due_tasks = [t for t in tasks if t.is_due(plan_date) and not t.completion_status]
        due_tasks.sort(key=lambda t: (-t.priority, t.time))
        due_tasks = self.sort_by_time(due_tasks)

        scheduled = []
        current_time = time(8, 0)
        total_time = 0
        for task in due_tasks:
            start = current_time
            end_dt = datetime.combine(plan_date, start) + timedelta(minutes=task.time)
            end = end_dt.time()
            scheduled.append({"task": task, "start_time": start, "end_time": end})
            current_time = end
            total_time += task.time

        explanation = f"Scheduled {len(scheduled)} tasks in priority order, starting at 8:00 AM."
        plan = DailyPlan(date=plan_date, scheduled_tasks=scheduled, total_time=total_time, explanation=explanation)
        plan.warnings = self.detect_conflicts(plan)
        return plan

    def generate_predictive_plan(self, plan_date: date) -> 'DailyPlan':
        """Generate a daily plan using predictive start times derived from task history."""
        tasks = self.owner.get_all_tasks()
        due_tasks = [t for t in tasks if t.is_due(plan_date) and not t.completion_status]

        predicted_schedule = []
        for task in due_tasks:
            predicted_start = self.predict_task_start_time(task, plan_date)
            predicted_schedule.append((task, predicted_start))

        predicted_schedule.sort(key=lambda item: (item[1].hour * 60 + item[1].minute, -item[0].priority))

        scheduled = []
        current_time = time(8, 0)
        total_time = 0
        confidences = []
        for task, predicted_start in predicted_schedule:
            candidate_start = predicted_start if predicted_start > current_time else current_time
            end_dt = datetime.combine(plan_date, candidate_start) + timedelta(minutes=task.time)
            end = end_dt.time()
            scheduled.append({"task": task, "start_time": candidate_start, "end_time": end})
            task.record_history(plan_date, candidate_start)
            current_time = end
            total_time += task.time
            confidences.append(task.predicted_confidence)

        average_confidence = float(statistics.mean(confidences)) if confidences else 0.0
        explanation = (
            f"Predicted optimal daily schedule using historical start times and preferred time windows. "
            f"Confidence: {average_confidence:.2f}."
        )
        plan = DailyPlan(
            date=plan_date,
            scheduled_tasks=scheduled,
            total_time=total_time,
            explanation=explanation,
            confidence_score=average_confidence,
        )
        plan.warnings = self.detect_conflicts(plan)
        return plan

    def optimize_schedule(self):
        """Placeholder for advanced schedule optimization logic."""
        pass

    def filter_tasks(self, completed: Optional[bool] = None, pet_name: Optional[str] = None) -> List[Task]:
        """Return tasks filtered by completion status and/or pet name."""
        tasks = self.owner.get_all_tasks()

        if pet_name is not None:
            matching_pet = next((pet for pet in self.owner.pets if pet.name == pet_name), None)
            tasks = matching_pet.tasks if matching_pet else []

        if completed is not None:
            tasks = [t for t in tasks if t.completion_status == completed]

        return tasks

@dataclass
class DailyPlan:
    date: date
    scheduled_tasks: List[Dict[str, Any]]
    total_time: int
    explanation: str
    warnings: List[str] = field(default_factory=list)

    def add_scheduled_task(self, task: Task, start_time: time, end_time: time):
        """Add a scheduled task with start and end times to the plan."""
        self.scheduled_tasks.append({"task": task, "start_time": start_time, "end_time": end_time})
        self.total_time += task.time

    def get_plan_summary(self) -> str:
        """Return a formatted string summary of the daily plan."""
        summary = f"Daily Plan for {self.date}:\n"
        for item in self.scheduled_tasks:
            task = item["task"]
            start = item["start_time"]
            end = item["end_time"]
            summary += f"- {task.description} ({start} - {end})\n"
        summary += f"Total time: {self.total_time} minutes\n"
        return summary

    def explain_plan(self) -> str:
        """Return the explanation of how the plan was generated."""
        return self.explanation
