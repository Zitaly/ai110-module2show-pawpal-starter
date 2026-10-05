"""PawPal+ core classes (skeleton based on diagrams/uml.mmd)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import IntEnum

# How many days apart each recurring task is due.
FREQUENCY_DAYS = {"daily": 1, "weekly": 7}


class Priority(IntEnum):
    """Task importance; higher values are scheduled first."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


def add_minutes(start: time, minutes: int) -> time:
    """Return `start` shifted by `minutes` (datetime.time can't do this directly)."""
    return (datetime.combine(date.min, start) + timedelta(minutes=minutes)).time()


def minutes_between(start: time, end: time) -> int:
    """Return the number of minutes from `start` to `end` on the same day."""
    return int((datetime.combine(date.min, end) - datetime.combine(date.min, start)).total_seconds() // 60)


@dataclass(eq=False)  # identity equality: two identical-looking tasks are still different tasks
class Task:
    """A single pet care activity, e.g. a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    preferred_time: time | None = None  # fixed start time; None means flexible
    frequency: str = "daily"  # a key of FREQUENCY_DAYS
    start_date: date = field(default_factory=date.today)  # anchor for recurrence
    last_completed: date | None = None
    pet_name: str = ""  # set by Pet.add_task

    def __post_init__(self) -> None:
        if isinstance(self.priority, str):  # accepts "low"/"medium"/"high", e.g. from the Streamlit selectbox
            try:
                self.priority = Priority[self.priority.upper()]
            except KeyError:
                raise ValueError(f"priority must be low, medium, or high, got {self.priority!r}") from None
        if self.duration_minutes <= 0:
            raise ValueError(f"duration_minutes must be positive, got {self.duration_minutes}")
        if self.frequency not in FREQUENCY_DAYS:
            raise ValueError(f"frequency must be one of {list(FREQUENCY_DAYS)}, got {self.frequency!r}")

    @property
    def label(self) -> str:
        """Unique-ish display name, e.g. "Mochi: Morning walk"."""
        return f"{self.pet_name}: {self.title}" if self.pet_name else self.title

    def mark_complete(self, day: date) -> None:
        """Record that this task was done on `day`."""
        pass

    def is_due(self, day: date) -> bool:
        """Return True if this task falls on `day` (per frequency/start_date) and isn't done yet that day."""
        pass


@dataclass(eq=False)
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet and set its pet_name."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove this exact task object from the pet."""
        pass

    def due_tasks(self, day: date) -> list[Task]:
        """Return this pet's tasks that are due on `day`."""
        pass


@dataclass
class Owner:
    """A pet owner, their pets, and their daily constraints."""

    name: str
    available_minutes: int = 120
    day_start: time = time(8, 0)
    prefer_high_priority_first: bool = True
    max_tasks_per_day: int | None = None  # None means no limit
    pets: list[Pet] = field(default_factory=list)
    schedules: dict[date, Schedule] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.available_minutes < 0:
            raise ValueError(f"available_minutes can't be negative, got {self.available_minutes}")

    @property
    def day_end(self) -> time:
        """Time when the owner's available window closes."""
        return add_minutes(self.day_start, self.available_minutes)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, pet: Pet) -> None:
        """Remove this exact pet object from the owner."""
        pass

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        pass

    def create_schedule(self, day: date) -> Schedule:
        """Create a Schedule for `day`, call generate(), store it (replacing any old one for that day), and return it."""
        pass


@dataclass
class Schedule:
    """A daily plan that orders an owner's tasks within their available time.

    Placement rule: tasks with a preferred_time are fixed at that time; flexible
    tasks then fill the remaining gaps from day_start, highest priority first.
    """

    day: date
    owner: Owner = field(repr=False, compare=False)  # avoids Owner <-> Schedule recursion
    planned: list[tuple[time, Task]] = field(default_factory=list)  # (start time, task) pairs
    skipped: list[Task] = field(default_factory=list)
    reasons: dict[str, str] = field(default_factory=dict)  # task.label -> why it was planned/skipped

    def generate(self) -> None:
        """Run the steps below in order to fill `planned`, `skipped`, and `reasons`."""
        pass

    def _collect_due_tasks(self) -> list[Task]:
        """Step 1: gather tasks from all pets that are due on `day`."""
        pass

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Step 2: order tasks by priority (respecting owner preferences), then by duration."""
        pass

    def _place_fixed_tasks(self, tasks: list[Task]) -> list[Task]:
        """Step 3: place tasks that have a preferred_time; skip ones outside the owner's window.

        Returns the remaining flexible tasks.
        """
        pass

    def _fill_flexible_tasks(self, tasks: list[Task]) -> None:
        """Step 4: pack flexible tasks into free gaps; skip ones that don't fit or exceed max_tasks_per_day."""
        pass

    def total_minutes(self) -> int:
        """Return the total duration of all planned tasks."""
        pass

    def has_conflicts(self) -> bool:
        """Return True if any planned tasks overlap in time (possible between fixed tasks)."""
        pass

    def explain(self) -> str:
        """Return a human-readable explanation built from `planned`, `skipped`, and `reasons`."""
        pass
