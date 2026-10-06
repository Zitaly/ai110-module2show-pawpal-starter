from datetime import date, time, timedelta

import pytest

from pawpal_system import Owner, Pet, Task

DAY = date(2026, 10, 5)  # a Monday


def make_owner(**kwargs) -> tuple[Owner, Pet]:
    owner = Owner("Jordan", available_minutes=kwargs.pop("available_minutes", 120), day_start=time(8, 0), **kwargs)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    return owner, pet


def starts(schedule) -> dict[str, str]:
    return {task.title: f"{start:%H:%M}" for start, task in schedule.planned}


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


# 1. Daily limit is applied after placement


def test_limit_ignores_tasks_that_could_not_be_placed():
    owner, pet = make_owner(max_tasks_per_day=2)
    pet.add_task(Task("Too early", 10, "high", preferred_time=time(6, 0), start_date=DAY))
    pet.add_task(Task("Walk", 20, "medium", start_date=DAY))
    pet.add_task(Task("Brush", 10, "low", start_date=DAY))

    schedule = owner.create_schedule(DAY)

    assert set(starts(schedule)) == {"Walk", "Brush"}
    assert [t.title for t in schedule.skipped] == ["Too early"]


def test_limit_cuts_lowest_ranked_placed_tasks():
    owner, pet = make_owner(max_tasks_per_day=1)
    pet.add_task(Task("Walk", 20, "high", start_date=DAY))
    brush = Task("Brush", 10, "low", start_date=DAY)
    pet.add_task(brush)

    schedule = owner.create_schedule(DAY)

    assert list(starts(schedule)) == ["Walk"]
    assert "daily limit" in schedule.reasons[brush]


# 2. Clashing fixed tasks are moved instead of overlapping


def test_clashing_fixed_task_moves_to_nearest_free_slot():
    owner, pet = make_owner()
    pet.add_task(Task("Breakfast", 30, "high", preferred_time=time(9, 0), start_date=DAY))
    meds = Task("Meds", 10, "low", preferred_time=time(9, 20), start_date=DAY)
    pet.add_task(meds)

    schedule = owner.create_schedule(DAY)

    assert starts(schedule) == {"Breakfast": "09:00", "Meds": "09:30"}
    assert not schedule.has_conflicts()
    assert "moved from preferred time 09:20" in schedule.reasons[meds]


def test_clashing_fixed_task_skipped_when_no_slot_fits():
    owner, pet = make_owner(available_minutes=30)
    pet.add_task(Task("Walk", 30, "high", preferred_time=time(8, 0), start_date=DAY))
    meds = Task("Meds", 10, "low", preferred_time=time(8, 10), start_date=DAY)
    pet.add_task(meds)

    schedule = owner.create_schedule(DAY)

    assert schedule.skipped == [meds]
    assert "no other free slot fits" in schedule.reasons[meds]


# 7. Missed occurrences carry over


def test_missed_weekly_task_stays_due_until_completed():
    task = Task("Bath", 30, frequency="weekly", start_date=DAY)
    wednesday = DAY + timedelta(days=2)

    assert task.is_due(wednesday)
    assert task.is_overdue(wednesday)

    task.mark_complete(wednesday)

    assert not task.is_due(wednesday)
    assert not task.is_due(DAY + timedelta(days=7))  # a completed occurrence never comes back


# Completing a recurring task creates the next occurrence


def test_completing_daily_task_creates_tomorrows_instance():
    _, pet = make_owner()
    walk = Task("Walk", 20, "high", preferred_time=time(9, 0), start_date=DAY)
    pet.add_task(walk)

    next_walk = pet.complete_task(walk, DAY)

    assert next_walk is not walk
    assert pet.tasks == [walk, next_walk]
    assert walk.is_completed(DAY)
    assert next_walk.start_date == DAY + timedelta(days=1)
    assert next_walk.last_completed is None
    assert (next_walk.title, next_walk.duration_minutes, next_walk.priority, next_walk.preferred_time, next_walk.pet_name) == (
        "Walk", 20, walk.priority, time(9, 0), "Mochi"
    )
    assert not next_walk.is_due(DAY)
    assert next_walk.is_due(DAY + timedelta(days=1))


def test_completing_weekly_task_late_keeps_its_weekday():
    _, pet = make_owner()
    bath = Task("Bath", 30, frequency="weekly", start_date=DAY)  # Monday
    pet.add_task(bath)

    next_bath = pet.complete_task(bath, DAY + timedelta(days=2))  # done Wednesday

    assert next_bath.start_date == DAY + timedelta(days=7)  # next Monday, not next Wednesday
    assert [t for t in pet.tasks if t.is_due(DAY + timedelta(days=7))] == [next_bath]


def test_completing_a_task_twice_is_rejected():
    _, pet = make_owner()
    walk = Task("Walk", 20, start_date=DAY)
    pet.add_task(walk)
    pet.complete_task(walk, DAY)

    with pytest.raises(ValueError, match="already completed"):
        pet.complete_task(walk, DAY)
    assert pet.task_count == 2


def test_completed_task_drops_out_of_schedule_and_next_one_appears():
    owner, pet = make_owner()
    walk = Task("Walk", 20, start_date=DAY)
    pet.add_task(walk)
    next_walk = pet.complete_task(walk, DAY)

    assert owner.create_schedule(DAY).planned == []
    assert [task for _, task in owner.create_schedule(DAY + timedelta(days=1)).planned] == [next_walk]


# Conflict detection


def test_conflict_between_pets_is_detected_and_reported():
    owner, mochi = make_owner()
    biscuit = Pet("Biscuit", "cat")
    owner.add_pet(biscuit)
    walk = Task("Walk", 30, "high", preferred_time=time(9, 0), start_date=DAY)
    meds = Task("Meds", 10, "low", preferred_time=time(9, 0), start_date=DAY)  # same start time
    mochi.add_task(walk)
    biscuit.add_task(meds)

    schedule = owner.create_schedule(DAY)

    assert schedule.conflicts == {meds: [walk]}
    assert schedule.conflict_messages() == ["Biscuit: Meds at 09:00 overlaps Mochi: Walk - moved to 08:50"]  # 10 min early beats 30 min late
    assert "Conflicts detected:" in schedule.explain()
    assert not schedule.has_conflicts()  # detected and resolved, so the final plan has no overlap


def test_conflict_reported_as_skipped_when_task_cannot_move():
    owner, pet = make_owner(available_minutes=30)
    walk = Task("Walk", 30, "high", preferred_time=time(8, 0), start_date=DAY)
    meds = Task("Meds", 10, "low", preferred_time=time(8, 10), start_date=DAY)
    pet.add_task(walk)
    pet.add_task(meds)

    schedule = owner.create_schedule(DAY)

    assert schedule.conflict_messages() == ["Mochi: Meds at 08:10 overlaps Mochi: Walk - skipped"]


def test_back_to_back_tasks_are_not_a_conflict():
    owner, pet = make_owner()
    pet.add_task(Task("Walk", 30, "high", preferred_time=time(9, 0), start_date=DAY))
    pet.add_task(Task("Meds", 10, "low", preferred_time=time(9, 30), start_date=DAY))

    schedule = owner.create_schedule(DAY)

    assert schedule.conflicts == {}
    assert list(starts(schedule).values()) == ["09:00", "09:30"]


def test_overdue_task_is_tagged_and_wins_priority_ties():
    owner, pet = make_owner(available_minutes=30)
    wednesday = DAY + timedelta(days=2)
    pet.add_task(Task("Walk", 30, "medium", start_date=wednesday))
    bath = Task("Bath", 30, "medium", frequency="weekly", start_date=DAY)
    pet.add_task(bath)

    schedule = owner.create_schedule(wednesday)

    assert list(starts(schedule)) == ["Bath"]
    assert "overdue since Mon Oct 05" in schedule.reasons[bath]


# Sorting by time


def test_planned_tasks_are_sorted_by_start_time():
    owner, pet = make_owner()
    pet.add_task(Task("Late", 10, "high", preferred_time=time(9, 30), start_date=DAY))
    pet.add_task(Task("Early", 10, "low", preferred_time=time(8, 5), start_date=DAY))
    pet.add_task(Task("Flexible", 5, "medium", start_date=DAY))

    schedule = owner.create_schedule(DAY)

    assert list(starts(schedule).values()) == ["08:00", "08:05", "09:30"]


# Filtering


def test_filter_tasks_by_pet_and_completion():
    owner, mochi = make_owner()
    biscuit = Pet("Biscuit", "cat")
    owner.add_pet(biscuit)
    walk = Task("Walk", 20, start_date=DAY)
    feed = Task("Feed", 5, start_date=DAY)
    brush = Task("Brush", 10, start_date=DAY)
    mochi.add_task(walk)
    mochi.add_task(feed)
    biscuit.add_task(brush)
    walk.mark_complete(DAY)

    assert owner.filter_tasks(pet_name="Mochi", day=DAY) == [walk, feed]
    assert owner.filter_tasks(completed=True, day=DAY) == [walk]
    assert owner.filter_tasks(completed=False, day=DAY) == [feed, brush]
    assert owner.filter_tasks(pet_name="Mochi", completed=False, day=DAY) == [feed]
    assert owner.filter_tasks(completed=True, day=DAY - timedelta(days=1)) == []  # not done yet as of the day before
