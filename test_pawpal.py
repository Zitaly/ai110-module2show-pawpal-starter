from datetime import date

from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status():
    day = date(2026, 10, 5)
    task = Task("Morning walk", 30, "high", start_date=day)
    assert task.last_completed is None
    assert task.is_due(day)

    task.mark_complete(day)

    assert task.last_completed == day
    assert not task.is_due(day)


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert pet.task_count == 0

    pet.add_task(Task("Breakfast", 10, "high"))

    assert pet.task_count == 1
