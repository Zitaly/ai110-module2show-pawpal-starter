import streamlit as st
from pawpal_system import Owner, Pet, Task, fmt

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# The Owner object holds all pets and tasks; keeping it in session_state lets it survive reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
owner: Owner = st.session_state.owner

st.subheader("Owner")
col1, col2, col3 = st.columns(3)
with col1:
    owner_name = st.text_input("Owner name", value=owner.name)
with col2:
    day_start = st.time_input("Day starts at", value=owner.day_start)
with col3:
    available_minutes = st.number_input(
        "Available minutes", min_value=0, max_value=24 * 60, value=owner.available_minutes, step=15
    )

try:
    Owner(owner_name, int(available_minutes), day_start)  # reuse Owner's validation before applying changes
    owner.name, owner.day_start, owner.available_minutes = owner_name, day_start, int(available_minutes)
except ValueError as e:
    st.error(f"Owner settings not saved: {e}")

st.markdown("### Pets")

col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    pet_age = st.number_input("Age (years)", min_value=0, max_value=40, value=3)

if st.button("Add pet"):
    try:
        owner.add_pet(Pet(pet_name.strip(), species, age=int(pet_age)))
        st.success(f"Added {pet_name}.")
    except ValueError as e:
        st.error(str(e))

if owner.pets:
    st.table([{"name": p.name, "species": p.species, "age": p.age, "tasks": p.task_count} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")

pets_by_name = {p.name: p for p in owner.pets}
if not owner.pets:
    st.caption("Add a pet before adding tasks.")
else:
    task_pet = st.selectbox("For pet", list(pets_by_name))

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col1, col2, col3 = st.columns(3)
    with col1:
        frequency = st.selectbox("Frequency", ["daily", "weekly"])
    with col2:
        has_fixed_time = st.checkbox("Fixed time?")
    with col3:
        preferred_time = st.time_input("Preferred time", value=owner.day_start, disabled=not has_fixed_time)

    if st.button("Add task"):
        try:
            pets_by_name[task_pet].add_task(
                Task(
                    task_title.strip(),
                    int(duration),
                    priority,
                    preferred_time=preferred_time if has_fixed_time else None,
                    frequency=frequency,
                )
            )
            st.success(f"Added {task_title} for {task_pet}.")
        except ValueError as e:
            st.error(str(e))

st.markdown("#### Task list")
view_day = st.date_input("Day", help="Task status, Done buttons, and the schedule below all use this day.")


def task_status(task: Task) -> str:
    """Short status of `task` as of view_day."""
    if task.is_completed(view_day):
        return "✅ done"
    if task.is_overdue(view_day):
        return f"⚠️ overdue since {task.start_date:%b %d}"
    if not task.is_due(view_day):
        return f"next due {task.start_date:%b %d}"
    return "⏳ due"


# "flexible" sorts after every HH:MM string, so flexible tasks come last when sorting by time.
SORT_KEYS = {
    "Pet": lambda t: (t.pet_name, t.title),
    "Time": lambda t: fmt(t.preferred_time) if t.preferred_time else "flexible",
    "Priority": lambda t: -t.priority,
    "Duration": lambda t: t.duration_minutes,
}
# Completed occurrences are kept as history, so hide them by default.
STATUS_FILTERS = {"Not completed": False, "Completed": True, "All": None}

if not owner.all_tasks():
    st.info("No tasks yet. Add one above.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All", *pets_by_name])
    with col2:
        status_filter = st.selectbox("Show status", list(STATUS_FILTERS))
    with col3:
        sort_by = st.selectbox("Sort by", list(SORT_KEYS))

    filtered = owner.filter_tasks(
        pet_name=None if pet_filter == "All" else pet_filter,
        completed=STATUS_FILTERS[status_filter],
        day=view_day,
    )
    if not filtered:
        st.info("No tasks match these filters.")
    # Buttons use on_click callbacks so the change is applied before the page redraws.
    for task in sorted(filtered, key=SORT_KEYS[sort_by]):
        info, status, done, remove = st.columns([5, 2, 1, 1])
        when = fmt(task.preferred_time) if task.preferred_time else "flexible"
        info.markdown(
            f"**{task.label}** · {task.duration_minutes} min · {task.priority.name.lower()} · {when} · {task.frequency}"
        )
        status.write(task_status(task))
        done.button(
            "Done",
            key=f"done-{id(task)}",
            disabled=not task.is_due(view_day),
            on_click=pets_by_name[task.pet_name].complete_task,  # also adds the next occurrence
            args=(task, view_day),
        )
        remove.button(
            "Remove",
            key=f"remove-{id(task)}",
            on_click=pets_by_name[task.pet_name].remove_task,
            args=(task,),
        )

st.divider()

st.subheader("Build Schedule")
st.caption(f"For {view_day:%A, %b %d %Y}. Change the day in the task list above.")

if st.button("Generate schedule"):
    schedule = owner.create_schedule(view_day)

    if schedule.planned:
        st.table(
            [
                {
                    "time": f"{start:%H:%M}",
                    "task": task.label,
                    "duration (min)": task.duration_minutes,
                    "priority": task.priority.name.lower(),
                    "why": schedule.reasons[task],
                }
                for start, task in schedule.planned
            ]
        )
        st.caption(f"{schedule.total_minutes()} of {owner.available_minutes} minutes used.")
    else:
        st.info("Nothing scheduled for this day.")

    if schedule.skipped:
        st.markdown("**Skipped**")
        st.table([{"task": t.label, "why": schedule.reasons[t]} for t in schedule.skipped])

    for message in schedule.conflict_messages():
        st.warning(f"Time conflict: {message}")

    if schedule.has_conflicts():
        st.warning("Some fixed-time tasks overlap. Adjust their preferred times.")

    with st.expander("Full explanation"):
        st.text(schedule.explain())
