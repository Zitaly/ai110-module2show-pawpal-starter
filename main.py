"""Demo: build an owner with two pets and print today's schedule."""

from datetime import date, time

from pawpal_system import Owner, Pet, Task


def main() -> None:
    today = date.today()

    owner = Owner("Jordan", available_minutes=180, day_start=time(7, 0))

    mochi = Pet("Mochi", "dog", age=3)
    biscuit = Pet("Biscuit", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    mochi.add_task(Task("Breakfast", 10, "high", preferred_time=time(7, 0)))
    mochi.add_task(Task("Morning walk", 30, "high", preferred_time=time(7, 30)))
    biscuit.add_task(Task("Medication", 5, "high", preferred_time=time(8, 15)))
    biscuit.add_task(Task("Brush coat", 15, "low"))  # flexible: fills the first free slot
    mochi.add_task(Task("Fetch in the yard", 20, "medium"))  # flexible

    schedule = owner.create_schedule(today)
    print(schedule.explain())


if __name__ == "__main__":
    main()
