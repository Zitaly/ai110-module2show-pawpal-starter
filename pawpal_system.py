"""PawPal+ core classes (skeleton based on diagrams/uml.mmd)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time


@dataclass
class Task:
    """A single pet care activity, e.g. a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low", "medium", or "high"
    preferred_time: time | None = None
    frequency: str = "daily"  # e.g. "daily", "weekly"
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def priority_rank(self) -> int:
        """Return a sortable number for this task's priority (higher = more important)."""
        pass

    def is_due(self, day: date) -> bool:
        """Return True if this task should be done on the given day."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        pass

    def pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        pass


@dataclass
class Owner:
    """A pet owner, their pets, and their daily constraints."""

    name: str
    available_minutes: int = 120
    day_start: time = time(8, 0)
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)
    schedules: list[Schedule] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        pass

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        pass

    def create_schedule(self, day: date) -> Schedule:
        """Build, store, and return a schedule for the given day."""
        pass


@dataclass
class Schedule:
    """A daily plan that orders an owner's tasks within their available time."""

    day: date
    owner: Owner = field(repr=False, compare=False)  # avoids Owner <-> Schedule recursion
    planned: list[tuple[time, Task]] = field(default_factory=list)  # (start time, task) pairs
    skipped: list[Task] = field(default_factory=list)

    def generate(self) -> None:
        """Choose and order tasks into `planned`; put tasks that don't fit into `skipped`."""
        pass

    def total_minutes(self) -> int:
        """Return the total duration of all planned tasks."""
        pass

    def has_conflicts(self) -> bool:
        """Return True if any planned tasks overlap in time."""
        pass

    def explain(self) -> str:
        """Return a human-readable explanation of why the plan looks the way it does."""
        pass
