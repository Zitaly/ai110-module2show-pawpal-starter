"""PawPal+ core classes (design in diagrams/uml.mmd)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import IntEnum

# How many days apart each recurring task is due.
FREQUENCY_DAYS = {"daily": 1, "weekly": 7}

MINUTES_PER_DAY = 24 * 60


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


def fmt(t: time) -> str:
    """Format a time as HH:MM."""
    return t.strftime("%H:%M")


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
        """Convert a string priority to Priority and validate duration and frequency."""
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
        """Display name, e.g. "Mochi: Morning walk"."""
        return f"{self.pet_name}: {self.title}" if self.pet_name else self.title

    def mark_complete(self, day: date) -> None:
        """Record that this task was done on `day`."""
        self.last_completed = day

    def is_due(self, day: date) -> bool:
        """Return True if this task falls on `day` (per frequency/start_date) and isn't done yet that day."""
        if day < self.start_date or self.last_completed == day:
            return False
        return (day - self.start_date).days % FREQUENCY_DAYS[self.frequency] == 0


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
        task.pet_name = self.name
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove this exact task object from the pet. Raises ValueError if it isn't there."""
        self.tasks.remove(task)

    def due_tasks(self, day: date) -> list[Task]:
        """Return this pet's tasks that are due on `day`."""
        return [task for task in self.tasks if task.is_due(day)]

    @property
    def task_count(self) -> int:
        """Number of care tasks assigned to this pet."""
        return len(self.tasks)


@dataclass
class Owner:
    """A pet owner, their pets, and their daily constraints."""

    name: str
    available_minutes: int = 120
    day_start: time = time(8, 0)
    prefer_high_priority_first: bool = True  # False: shortest tasks first, to fit as many as possible
    max_tasks_per_day: int | None = None  # None means no limit
    pets: list[Pet] = field(default_factory=list)
    schedules: dict[date, Schedule] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate that the available time is non-negative and ends before midnight."""
        if self.available_minutes < 0:
            raise ValueError(f"available_minutes can't be negative, got {self.available_minutes}")
        if minutes_between(time(0, 0), self.day_start) + self.available_minutes >= MINUTES_PER_DAY:
            raise ValueError("available time must end before midnight")

    @property
    def day_end(self) -> time:
        """Time when the owner's available window closes."""
        return add_minutes(self.day_start, self.available_minutes)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner. Pet names must be unique so task labels stay unambiguous."""
        if pet in self.pets:
            return
        if any(existing.name == pet.name for existing in self.pets):
            raise ValueError(f"{self.name} already has a pet named {pet.name!r}")
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove this exact pet object from the owner. Raises ValueError if it isn't there."""
        self.pets.remove(pet)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def create_schedule(self, day: date) -> Schedule:
        """Create a Schedule for `day`, call generate(), store it (replacing any old one for that day), and return it."""
        schedule = Schedule(day, self)
        schedule.generate()
        self.schedules[day] = schedule
        return schedule


@dataclass
class Schedule:
    """A daily plan that orders an owner's tasks within their available time.

    Placement rule: tasks with a preferred_time are fixed at that time; flexible
    tasks then fill the remaining gaps from day_start, highest priority first.
    """

    day: date
    owner: Owner = field(repr=False, compare=False)  # avoids Owner <-> Schedule recursion
    planned: list[tuple[time, Task]] = field(default_factory=list)  # (start time, task) pairs, sorted by time
    skipped: list[Task] = field(default_factory=list)
    reasons: dict[Task, str] = field(default_factory=dict)  # why each task was planned or skipped

    def generate(self) -> None:
        """Run the steps below in order to fill `planned`, `skipped`, and `reasons`."""
        self.planned.clear()
        self.skipped.clear()
        self.reasons.clear()

        tasks = self._sort_tasks(self._collect_due_tasks())

        limit = self.owner.max_tasks_per_day
        if limit is not None:
            for task in tasks[limit:]:
                self._skip(task, f"over the daily limit of {limit} tasks")
            tasks = tasks[:limit]

        flexible = self._place_fixed_tasks(tasks)
        self._fill_flexible_tasks(flexible)
        self.planned.sort(key=lambda entry: entry[0])

    def _collect_due_tasks(self) -> list[Task]:
        """Step 1: gather tasks from all pets that are due on `day`."""
        return [task for pet in self.owner.pets for task in pet.due_tasks(self.day)]

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Step 2: order tasks by priority (respecting owner preferences), then by duration."""
        if self.owner.prefer_high_priority_first:
            return sorted(tasks, key=lambda t: (-t.priority, t.duration_minutes))
        return sorted(tasks, key=lambda t: (t.duration_minutes, -t.priority))

    def _place_fixed_tasks(self, tasks: list[Task]) -> list[Task]:
        """Step 3: place tasks that have a preferred_time; skip ones outside the owner's window.

        Returns the remaining flexible tasks.
        """
        window_start, window_end = self.owner.day_start, self.owner.day_end
        flexible = []
        for task in tasks:
            if task.preferred_time is None:
                flexible.append(task)
                continue
            start = task.preferred_time
            end = add_minutes(start, task.duration_minutes)
            if start < window_start or end > window_end or end < start:
                self._skip(task, f"fixed at {fmt(start)}, outside available time {fmt(window_start)}-{fmt(window_end)}")
                continue
            clashes = [other for other_start, other in self.planned if self._overlaps(start, task, other_start, other)]
            reason = f"fixed at preferred time {fmt(start)}"
            if clashes:
                reason += f" (CONFLICT with {', '.join(other.label for other in clashes)})"
                for other in clashes:
                    self.reasons[other] += f" (CONFLICT with {task.label})"
            self._plan(start, task, reason)
        return flexible

    def _fill_flexible_tasks(self, tasks: list[Task]) -> None:
        """Step 4: pack flexible tasks into free gaps; skip ones that don't fit."""
        gaps = self._free_gaps()  # [start, end] offsets in minutes from day_start
        for task in tasks:
            gap = next((g for g in gaps if g[1] - g[0] >= task.duration_minutes), None)
            if gap is None:
                largest = max((g[1] - g[0] for g in gaps), default=0)
                self._skip(task, f"needs {task.duration_minutes} min, largest free slot is {largest} min")
                continue
            start = add_minutes(self.owner.day_start, gap[0])
            self._plan(start, task, f"{task.priority.name.lower()} priority, placed in earliest free slot")
            gap[0] += task.duration_minutes

    def _free_gaps(self) -> list[list[int]]:
        """Return free [start, end] intervals (minute offsets from day_start) not used by planned tasks."""
        busy = sorted(
            (minutes_between(self.owner.day_start, start), minutes_between(self.owner.day_start, start) + task.duration_minutes)
            for start, task in self.planned
        )
        gaps, cursor = [], 0
        for busy_start, busy_end in busy:
            if busy_start > cursor:
                gaps.append([cursor, busy_start])
            cursor = max(cursor, busy_end)
        if cursor < self.owner.available_minutes:
            gaps.append([cursor, self.owner.available_minutes])
        return gaps

    @staticmethod
    def _overlaps(start_a: time, task_a: Task, start_b: time, task_b: Task) -> bool:
        """Return True if the two scheduled tasks share any time."""
        return start_a < add_minutes(start_b, task_b.duration_minutes) and start_b < add_minutes(start_a, task_a.duration_minutes)

    def _plan(self, start: time, task: Task, reason: str) -> None:
        """Add `task` to the plan at `start` and record why."""
        self.planned.append((start, task))
        self.reasons[task] = reason

    def _skip(self, task: Task, reason: str) -> None:
        """Mark `task` as skipped and record why."""
        self.skipped.append(task)
        self.reasons[task] = reason

    def total_minutes(self) -> int:
        """Return the total duration of all planned tasks."""
        return sum(task.duration_minutes for _, task in self.planned)

    def has_conflicts(self) -> bool:
        """Return True if any planned tasks overlap in time (possible between fixed tasks)."""
        latest_end = None
        for start, task in sorted(self.planned, key=lambda entry: entry[0]):
            if latest_end is not None and start < latest_end:
                return True
            end = add_minutes(start, task.duration_minutes)
            latest_end = end if latest_end is None else max(latest_end, end)
        return False

    def explain(self) -> str:
        """Return a human-readable explanation built from `planned`, `skipped`, and `reasons`."""
        owner = self.owner
        lines = [
            f"Plan for {owner.name} on {self.day:%A, %b %d %Y} "
            f"(available {fmt(owner.day_start)}-{fmt(owner.day_end)}, {owner.available_minutes} min):"
        ]
        if not self.planned and not self.skipped:
            lines.append("  No tasks are due today.")
            return "\n".join(lines)

        for start, task in self.planned:
            end = add_minutes(start, task.duration_minutes)
            lines.append(
                f"  {fmt(start)}-{fmt(end)}  {task.label} ({task.duration_minutes} min) "
                f"[{task.priority.name.lower()}] - {self.reasons[task]}"
            )
        lines.append(f"Total: {self.total_minutes()} of {owner.available_minutes} min used.")

        if self.skipped:
            lines.append("Skipped:")
            lines.extend(f"  {task.label} - {self.reasons[task]}" for task in self.skipped)
        if self.has_conflicts():
            lines.append("Warning: some fixed-time tasks overlap. Adjust their preferred times.")
        return "\n".join(lines)
