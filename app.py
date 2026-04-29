import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler
from datetime import date

# Initialize Owner in session_state if not present
if 'owner' not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan",
        available_hours_per_day=8,
        preferred_start_time="8:00 AM",
        preferred_end_time="6:00 PM",
        preferences={}
    )

# Initialize Scheduler
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = Scheduler(owner=st.session_state.owner, constraints={})

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+
"""
)

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
age = st.number_input("Pet age", min_value=0, max_value=30, value=2)

if st.button("Add Pet"):
    pet = Pet(name=pet_name, species=species, age=age, special_needs=[])
    st.session_state.owner.add_pet(pet)
    st.success(f"Added pet {pet_name} ({species}, age {age})")
    st.rerun()  # Refresh to update UI

# Display current pets
if st.session_state.owner.pets:
    st.write("Current Pets:")
    for pet in st.session_state.owner.pets:
        st.write(f"- {pet.name} ({pet.species}, age {pet.age})")
else:
    st.info("No pets added yet.")

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if st.session_state.owner.pets:
    pet_options = [pet.name for pet in st.session_state.owner.pets]
    selected_pet_name = st.selectbox("Select Pet for Task", pet_options)
    selected_pet = next(pet for pet in st.session_state.owner.pets if pet.name == selected_pet_name)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", [1, 2, 3, 4, 5], index=4)  # 1 low, 5 high
    with col4:
        category = st.selectbox("Category", ["exercise", "feeding", "grooming", "other"])

    if st.button("Add Task"):
        task = Task(
            description=task_title,
            category=category,
            time=duration,
            priority=priority,
            frequency="daily",
            preferred_time="morning"
        )
        selected_pet.add_task(task)
        st.success(f"Added task '{task_title}' to {selected_pet_name}")
        st.rerun()
else:
    st.warning("Add a pet first before adding tasks.")

# Display current tasks for all pets
if st.session_state.owner.pets:
    st.write("Current Tasks:")
    for pet in st.session_state.owner.pets:
        if pet.tasks:
            st.write(f"**{pet.name}**:")
            for task in pet.tasks:
                st.write(f"- {task.description} ({task.time} min, priority {task.priority})")
        else:
            st.write(f"**{pet.name}**: No tasks yet.")
else:
    st.info("No pets, no tasks.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

use_predictive = st.checkbox("Use predictive scheduling", value=True)

if st.button("Generate Schedule"):
    if st.session_state.owner.pets and any(pet.tasks for pet in st.session_state.owner.pets):
        if use_predictive:
            plan = st.session_state.scheduler.generate_predictive_plan(date.today())
        else:
            plan = st.session_state.scheduler.generate_daily_plan(date.today())

        # Show conflict warnings clearly
        if plan.warnings:
            for warning in plan.warnings:
                st.warning(warning)

        # Display summary as a table
        schedule_rows = []
        for item in plan.scheduled_tasks:
            schedule_rows.append({
                "Task": item["task"].description,
                "Pet": next((pet.name for pet in st.session_state.owner.pets if item["task"] in pet.tasks), "Unknown"),
                "Start": item["start_time"].strftime("%H:%M"),
                "End": item["end_time"].strftime("%H:%M"),
                "Priority": item["task"].priority,
                "Duration": item["task"].time,
                "Confidence": f"{item['task'].predicted_confidence:.2f}" if hasattr(item['task'], 'predicted_confidence') else "N/A",
            })
        if schedule_rows:
            st.success("Schedule generated successfully.")
            st.table(schedule_rows)
            st.info(plan.explain_plan())
            if hasattr(plan, "confidence_score") and plan.confidence_score > 0:
                st.caption(f"Predictive confidence: {plan.confidence_score:.2f}")
        else:
            st.info("No tasks to schedule for today.")

        # Also show sorted tasks for reference
        sorted_tasks = st.session_state.scheduler.sort_by_time(st.session_state.owner.get_all_tasks())
        st.subheader("Tasks sorted by duration")
        st.table([{"Task": t.description, "Duration": t.time, "Priority": t.priority} for t in sorted_tasks])
    else:
        st.warning("Add pets and tasks first.")
