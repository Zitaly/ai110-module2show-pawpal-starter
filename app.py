import pandas as pd
import streamlit as st
from pawpal_system import Owner, Pet, Priority, Task, add_minutes, fmt

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
    owner.set_window(day_start, int(available_minutes))  # validates before applying either value
    owner.name = owner_name
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
    st.table(
        pd.DataFrame(
            {"Pet": p.name, "Species": p.species.capitalize(), "Age": p.age, "Tasks": p.task_count} for p in owner.pets
        ).set_index("Pet")
    )
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


PRIORITY_BADGES = {Priority.HIGH: "🔴 High", Priority.MEDIUM: "🟡 Medium", Priority.LOW: "🟢 Low"}


def task_status(task: Task) -> str:
    """Short status of `task` as of view_day."""
    if task.is_completed(view_day):
        return "✅ Done"
    if task.is_overdue(view_day):
        return f"⚠️ Overdue since {task.start_date:%b %d}"
    if not task.is_due(view_day):
        return f"🗓️ Next due {task.start_date:%b %d}"
    return "⏳ Due"


def when(task: Task) -> str:
    """The task's fixed time, or "flexible"."""
    return fmt(task.preferred_time) if task.preferred_time else "flexible"


def complete(task: Task) -> None:
    """Button callback: complete `task` on view_day and leave a message for the next run."""
    next_task = task.pet.complete_task(task, view_day)  # also adds the next occurrence
    st.session_state.flash = f"Marked {task.label} done. Next due {next_task.start_date:%a %b %d}."


def remove(task: Task) -> None:
    """Button callback: remove `task` from its pet and leave a message for the next run."""
    label = task.label
    task.pet.remove_task(task)
    st.session_state.flash = f"Removed {label}."


# "flexible" sorts after every HH:MM string, so flexible tasks come last when sorting by time.
SORT_KEYS = {
    "Time": when,
    "Pet": lambda t: (t.pet_name, t.title),
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
    filtered.sort(key=SORT_KEYS[sort_by])

    if not filtered:
        st.info("No tasks match these filters.")
    else:
        st.table(
            pd.DataFrame(
                {
                    "Time": when(task),
                    "Task": task.label,
                    "Minutes": task.duration_minutes,
                    "Priority": PRIORITY_BADGES[task.priority],
                    "Repeats": task.frequency,
                    "Status": task_status(task),
                }
                for task in filtered
            ).set_index("Time")
        )

        overdue = sum(task.is_overdue(view_day) for task in filtered)
        if overdue:
            count = "1 task is" if overdue == 1 else f"{overdue} tasks are"
            st.warning(f"{count} overdue. Overdue tasks win priority ties in the schedule until marked done.")
        else:
            # Judge "caught up" on every task for the chosen pet(s), not just the rows the status filter shows.
            pet_tasks = owner.filter_tasks(pet_name=None if pet_filter == "All" else pet_filter, day=view_day)
            if not any(t.is_due(view_day) for t in pet_tasks) and any(t.is_completed(view_day) for t in pet_tasks):
                st.success(f"All caught up for {view_day:%b %d}.")

        # Buttons use on_click callbacks so the change is applied before the page redraws.
        picked_col, done_col, remove_col = st.columns([4, 1, 1], vertical_alignment="bottom")
        with picked_col:
            # Pick by position: Streamlit deep-copies widget values, so selecting the Task itself would return a copy.
            picked = filtered[
                st.selectbox(
                    "Task",
                    range(len(filtered)),
                    format_func=lambda i: f"{filtered[i].label} · {when(filtered[i])} · {task_status(filtered[i])}",
                )
            ]
        done_col.button(
            "Mark done",
            disabled=not picked.is_due(view_day),
            on_click=complete,
            args=(picked,),
        )
        remove_col.button("Remove", on_click=remove, args=(picked,))

    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))

st.divider()

st.subheader("Build Schedule")
st.caption(f"For {view_day:%A, %b %d %Y}. Change the day in the task list above.")

if st.button("Generate schedule"):
    schedule = owner.create_schedule(view_day)

    planned, skipped = len(schedule.planned), len(schedule.skipped)
    used = f"{schedule.total_minutes()} of {owner.available_minutes} min used"

    if not planned and not skipped:
        st.info("No tasks are due on this day.")
    elif not skipped:
        st.success(f"All {planned} due task{'s' if planned != 1 else ''} fit in the day ({used}).")
    else:
        st.warning(f"Planned {planned} of {planned + skipped} due tasks ({used}). {skipped} didn't fit; see below.")

    if planned:
        st.table(
            pd.DataFrame(
                {
                    "Time": f"{fmt(start)}–{fmt(add_minutes(start, task.duration_minutes))}",
                    "Task": task.label,
                    "Minutes": task.duration_minutes,
                    "Priority": PRIORITY_BADGES[task.priority],
                    "Why": schedule.reasons[task],
                }
                for start, task in schedule.planned
            ).set_index("Time")
        )

    if skipped:
        st.markdown("**Skipped**")
        st.table(
            pd.DataFrame(
                {"Task": t.label, "Priority": PRIORITY_BADGES[t.priority], "Why": schedule.reasons[t]}
                for t in schedule.skipped
            ).set_index("Task")
        )

    for message in schedule.conflict_messages():
        st.warning(f"Time conflict: {message}")

    if schedule.has_conflicts():
        st.error("Some planned tasks still overlap. Adjust their preferred times.")

    with st.expander("Full explanation"):
        st.text(schedule.explain())
