import pytest
from pawpal_system import Task, Pet, Owner, Scheduler, DailyPlan
from datetime import date, time, timedelta

def test_task_completion():
    """Verify that calling mark_complete() changes the task's completion status."""
    task = Task(
        description="Test Task",
        category="test",
        time=10,
        priority=3,
        frequency="daily",
        preferred_time="morning"
    )
    # Initially not complete
    assert not task.completion_status
    # Mark as complete
    task.mark_complete()
    # Now should be complete
    assert task.completion_status

def test_task_addition():
    """Verify that adding a task to a Pet increases the pet's task count."""
    pet = Pet(
        name="Test Pet",
        species="Dog",
        age=2,
        special_needs=[]
    )
    initial_count = len(pet.tasks)
    task = Task(
        description="New Task",
        category="exercise",
        time=20,
        priority=4,
        frequency="daily",
        preferred_time="afternoon"
    )
    pet.add_task(task)
    assert len(pet.tasks) == initial_count + 1


def test_sort_by_time_correctness():
    """Verify tasks are returned in chronological order by time duration."""
    owner = Owner(name="Jane", available_hours_per_day=8, preferred_start_time="8:00 AM", preferred_end_time="6:00 PM", preferences={})
    scheduler = Scheduler(owner=owner, constraints={})

    t1 = Task(description="Long Task", category="grooming", time=60, priority=2, frequency="daily", preferred_time="morning")
    t2 = Task(description="Short Task", category="feeding", time=10, priority=3, frequency="daily", preferred_time="morning")
    t3 = Task(description="Medium Task", category="play", time=30, priority=1, frequency="daily", preferred_time="afternoon")

    owner.add_pet(Pet(name="Fluffy", species="Cat", age=2, special_needs=[]))
    owner.pets[0].add_task(t1)
    owner.pets[0].add_task(t2)
    owner.pets[0].add_task(t3)

    ordered = scheduler.sort_by_time(owner.get_all_tasks())
    assert [t.description for t in ordered] == ["Short Task", "Medium Task", "Long Task"]


def test_recurrence_logic_daily():
    """Confirm that marking a daily task complete creates a new task for next day."""
    task = Task(description="Walk", category="exercise", time=20, priority=5, frequency="daily", preferred_time="morning", due_date=date.today())
    next_task = task.mark_complete()

    assert task.completion_status
    assert next_task is not None
    assert next_task.frequency == "daily"
    assert next_task.due_date == date.today() + timedelta(days=1)


def test_conflict_detection_duplicate_time():
    """Verify that Scheduler flags duplicate task times as conflict warnings."""
    owner = Owner(name="Sam", available_hours_per_day=8, preferred_start_time="8:00 AM", preferred_end_time="6:00 PM", preferences={})
    scheduler = Scheduler(owner=owner, constraints={})
    plan = DailyPlan(date=date.today(), scheduled_tasks=[], total_time=0, explanation="test")

    t1 = Task(description="Breakfast", category="feeding", time=15, priority=4, frequency="daily", preferred_time="morning")
    t2 = Task(description="Admin", category="meds", time=15, priority=4, frequency="daily", preferred_time="morning")

    plan.add_scheduled_task(t1, time(8, 0), time(8, 15))
    plan.add_scheduled_task(t2, time(8, 0), time(8, 15))

    conflicts = scheduler.detect_conflicts(plan)
    assert len(conflicts) >= 1
    assert "overlaps" in conflicts[0]


def test_predictive_plan_uses_history():
    """Verify predictive schedule uses history and returns a confidence score."""
    owner = Owner(name="Sam", available_hours_per_day=8, preferred_start_time="8:00 AM", preferred_end_time="6:00 PM", preferences={})
    pet = Pet(name="Buddy", species="Dog", age=4, special_needs=[])
    owner.add_pet(pet)

    task = Task(description="Walk", category="exercise", time=20, priority=5, frequency="daily", preferred_time="morning")
    task.history = [
        {"date": date.today(), "start_time": time(8, 0), "duration": 20},
        {"date": date.today() - timedelta(days=1), "start_time": time(8, 15), "duration": 20},
    ]
    pet.add_task(task)

    scheduler = Scheduler(owner=owner, constraints={})
    plan = scheduler.generate_predictive_plan(date.today())

    assert plan.scheduled_tasks[0]["start_time"] >= time(8, 0)
    assert plan.confidence_score > 0.3
    assert "Predicted optimal daily schedule" in plan.explanation


def test_generate_predictive_plan_without_history():
    """Verify the scheduler falls back cleanly when no history exists."""
    owner = Owner(name="Ava", available_hours_per_day=8, preferred_start_time="8:00 AM", preferred_end_time="6:00 PM", preferences={})
    pet = Pet(name="Kitty", species="Cat", age=2, special_needs=[])
    owner.add_pet(pet)

    task = Task(description="Feed", category="feeding", time=10, priority=4, frequency="daily", preferred_time="morning")
    pet.add_task(task)

    scheduler = Scheduler(owner=owner, constraints={})
    plan = scheduler.generate_predictive_plan(date.today())

    assert plan.scheduled_tasks[0]["task"].description == "Feed"
    assert plan.confidence_score >= 0.35
    assert not plan.warnings

