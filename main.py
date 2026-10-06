"""Demo: build an owner with two pets, add tasks out of order, then sort, filter, and schedule them."""

from datetime import date, time

from pawpal_system import Owner, Pet, Task, fmt


def print_tasks(heading: str, tasks: list[Task], day: date) -> None:
    """Print one line per task with its time and completion status."""
    print(heading)
    if not tasks:
        print("  (none)")
    for task in tasks:
        when = fmt(task.preferred_time) if task.preferred_time else "flexible"
        status = "done" if task.is_completed(day) else "not done"
        print(f"  {when:>8}  {task.label} ({status})")
    print()


def main() -> None:
    today = date.today()

    owner = Owner("Jordan", available_minutes=180, day_start=time(7, 0))

    mochi = Pet("Mochi", "dog", age=3)
    biscuit = Pet("Biscuit", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    # Added deliberately out of time order, alternating pets.
    biscuit.add_task(Task("Medication", 5, "high", preferred_time=time(8, 15)))
    mochi.add_task(Task("Fetch in the yard", 20, "medium"))  # flexible
    mochi.add_task(Task("Morning walk", 30, "high", preferred_time=time(7, 30)))
    biscuit.add_task(Task("Brush coat", 15, "low"))  # flexible
    mochi.add_task(Task("Evening walk", 30, "medium", preferred_time=time(9, 15)))
    mochi.add_task(Task("Breakfast", 10, "high", preferred_time=time(7, 0)))
    biscuit.add_task(Task("Litter box", 10, "medium", preferred_time=time(7, 45)))

    print_tasks("All tasks, in the order they were added:", owner.all_tasks(), today)

    # Same HH:MM key as Schedule.sort_by_time; "flexible" sorts after every HH:MM string.
    by_time = sorted(owner.all_tasks(), key=lambda t: fmt(t.preferred_time) if t.preferred_time else "flexible")
    print_tasks("All tasks, sorted by preferred time:", by_time, today)

    # Finish a couple of tasks; each completion adds that task's next occurrence.
    for pet in owner.pets:
        for task in list(pet.tasks):
            if task.title in ("Breakfast", "Medication"):
                next_task = pet.complete_task(task, today)
                print(f"Completed {task.label}; next one added for {next_task.start_date:%a %b %d}.")
    print()

    print_tasks("Mochi's tasks:", owner.filter_tasks(pet_name="Mochi", day=today), today)
    print_tasks("Biscuit's tasks:", owner.filter_tasks(pet_name="Biscuit", day=today), today)
    print_tasks("Completed today:", owner.filter_tasks(completed=True, day=today), today)
    print_tasks("Still to do:", owner.filter_tasks(completed=False, day=today), today)
    print_tasks("Mochi, still to do:", owner.filter_tasks(pet_name="Mochi", completed=False, day=today), today)

    # The schedule only includes tasks still due, placed and then sorted by start time.
    schedule = owner.create_schedule(today)
    print(schedule.explain())


if __name__ == "__main__":
    main()
