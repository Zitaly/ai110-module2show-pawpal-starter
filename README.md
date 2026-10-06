# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Plan for Jordan on Monday, Oct 05 2026 (available 07:00-10:00, 180 min):
  07:00-07:10  Mochi: Breakfast (10 min) [high] - fixed at preferred time 07:00
  07:10-07:30  Mochi: Fetch in the yard (20 min) [medium] - medium priority, placed in earliest free slot
  07:30-08:00  Mochi: Morning walk (30 min) [high] - fixed at preferred time 07:30
  08:00-08:15  Biscuit: Brush coat (15 min) [low] - low priority, placed in earliest free slot
  08:15-08:20  Biscuit: Medication (5 min) [high] - fixed at preferred time 08:15
Total: 80 of 180 min used.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run with coverage:
pytest --cov
```
The 52 tests of tthe suite cover a wide range of the app's functions.

Sample test output:

```
52 passed in 0.22s
```

While 52 tests were passed, since this is AI-generated code, I'd give it a confidence rating of 3.

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | sort_by_time(self) | by time. |
| Filtering | filter_tasks| by pet name, completion, or time. |
| Conflict handling | has_conflicts(self) and _relocate(self, task: Task) | Checks if there's a conflict and relocates a task respectively. |
| Recurring tasks | complete_task(self, task: Task, day: date) | Marks task as complete and sets up a new task for its next occurrence.|

## 📸 Demo Walkthrough

```bash
streamlit run app.py   # the interactive app
python main.py         # the command-line demo
```

### UI features and actions

The app is one page, top to bottom:

| Section | What you see | What you can do |
|---------|--------------|-----------------|
| **Owner** | Name, day start time, available minutes | Edit any field. The window must end before midnight; an invalid combination shows an error and isn't saved. |
| **Pets** | Table of pets with species, age, and task count | Add a pet (name, species, age). Duplicate pet names are rejected. |
| **Tasks** | Form for a new task | Pick the pet, then set title, duration, priority (low/medium/high), frequency (daily/weekly), and optionally a fixed time. Leave "Fixed time?" unchecked for a flexible task. |
| **Task list** | Table of tasks with time, minutes, priority badge (🔴 / 🟡 / 🟢), frequency, and status (⏳ Due, ⚠️ Overdue, ✅ Done, 🗓️ Next due) | Choose the **Day** to view; filter by pet and by status (not completed / completed / all); sort by time, pet, priority, or duration. Pick a task below the table and press **Mark done** (only enabled when it's due) or **Remove**. |
| **Build Schedule** | Summary banner, plan table, skipped table, conflict warnings, full text explanation | Press **Generate schedule** to plan the chosen day. |

Status messages: green banners confirm actions ("Marked Mochi: Morning walk done. Next due Wed Oct 07.") and full schedules; yellow banners flag overdue tasks, tasks that didn't fit, and time conflicts that were resolved.

### Example workflow

Dates below are from a run on Tuesday, Oct 06 2026; the app uses today's date.

1. Run `streamlit run app.py`. Under **Owner**, set the day to start at **07:00** with **180** available minutes.
2. Under **Pets**, add **Mochi** (dog, 3) and **Biscuit** (cat, 5). Both appear in the pets table with 0 tasks.
3. Under **Tasks**, add:
   - Mochi: *Morning walk*, 30 min, high, daily, fixed at 07:30
   - Biscuit: *Litter box*, 10 min, medium, daily, fixed at 07:45
   - Mochi: *Fetch in the yard*, 20 min, medium, daily, flexible
   - Biscuit: *Brush coat*, 15 min, low, weekly, flexible
4. The **Task list** shows all four sorted by time, with flexible tasks last. Set **Show pet** to Biscuit to see only *Litter box* and *Brush coat*, then set it back to All.
5. Press **Generate schedule**. The banner reads *"All 4 due tasks fit in the day (75 of 180 min used)."* and the plan is:

   | Time | Task | Why |
   |------|------|-----|
   | 07:00–07:20 | Mochi: Fetch in the yard | medium priority, placed in earliest free slot |
   | 07:30–08:00 | Mochi: Morning walk | fixed at preferred time 07:30 |
   | 08:00–08:10 | Biscuit: Litter box | moved from preferred time 07:45 to avoid Mochi: Morning walk |
   | 08:10–08:25 | Biscuit: Brush coat | low priority, placed in earliest free slot |

   A warning explains the clash: *"Biscuit: Litter box at 07:45 overlaps Mochi: Morning walk - moved to 08:00"*.
6. In the task picker, choose *Mochi: Morning walk* and press **Mark done**. The app confirms *"Next due Wed Oct 07"*, and the walk's status changes to 🗓️ Next due Oct 07. Set **Show status** to Completed to see it marked ✅ Done, then switch back.
7. Change **Day** to two days later (Oct 08) without completing anything else. A warning reports *"4 tasks are overdue"*. Generating the schedule again places them the same way, each tagged with *"(overdue since …)"*.

### Key scheduler behaviors

- **Fixed before flexible.** Tasks with a preferred time are placed first at that time; flexible tasks then fill the remaining gaps from the start of the day.
- **Priority order.** Higher priority is placed first; within a priority, shorter tasks go first, and overdue tasks win ties. (`Owner.prefer_high_priority_first = False` switches to shortest-first.)
- **Conflict resolution.** A fixed task that overlaps a higher-ranked one is moved to the free slot nearest its preferred time (the earlier slot on a tie), or skipped if nothing fits. Every move is reported.
- **Skipping with reasons.** Tasks outside the owner's window or too long for any free slot are listed under *Skipped* with the reason, e.g. *"needs 15 min, largest free slot is 10 min"*.
- **Recurrence.** Marking a task done creates its next occurrence. Weekly tasks keep their weekday even if done late, and a task missed for several weeks creates only one next occurrence.
- **Carry-over.** An occurrence that isn't done stays due (and overdue) on later days until it's completed.
- **Daily limit.** `Owner.max_tasks_per_day` caps how many tasks are planned, keeping the highest-ranked ones. It's set in code; the app doesn't expose it yet.

### Sample CLI output (`python main.py`)

`main.py` builds the same owner and pets, adds seven tasks out of order, sorts and filters them, completes *Breakfast* and *Medication*, then prints the day's plan:

```
All tasks, in the order they were added:
  flexible  Mochi: Fetch in the yard (not done)
     07:30  Mochi: Morning walk (not done)
     09:15  Mochi: Evening walk (not done)
     07:00  Mochi: Breakfast (not done)
     08:15  Biscuit: Medication (not done)
  flexible  Biscuit: Brush coat (not done)
     07:45  Biscuit: Litter box (not done)

All tasks, sorted by preferred time:
     07:00  Mochi: Breakfast (not done)
     07:30  Mochi: Morning walk (not done)
     07:45  Biscuit: Litter box (not done)
     08:15  Biscuit: Medication (not done)
     09:15  Mochi: Evening walk (not done)
  flexible  Mochi: Fetch in the yard (not done)
  flexible  Biscuit: Brush coat (not done)

Completed Mochi: Breakfast; next one added for Wed Oct 07.
Completed Biscuit: Medication; next one added for Wed Oct 07.

Mochi's tasks:
  flexible  Mochi: Fetch in the yard (not done)
     07:30  Mochi: Morning walk (not done)
     09:15  Mochi: Evening walk (not done)
     07:00  Mochi: Breakfast (done)
     07:00  Mochi: Breakfast (not done)

Biscuit's tasks:
     08:15  Biscuit: Medication (done)
  flexible  Biscuit: Brush coat (not done)
     07:45  Biscuit: Litter box (not done)
     08:15  Biscuit: Medication (not done)

Completed today:
     07:00  Mochi: Breakfast (done)
     08:15  Biscuit: Medication (done)

Still to do:
  flexible  Mochi: Fetch in the yard (not done)
     07:30  Mochi: Morning walk (not done)
     09:15  Mochi: Evening walk (not done)
     07:00  Mochi: Breakfast (not done)
  flexible  Biscuit: Brush coat (not done)
     07:45  Biscuit: Litter box (not done)
     08:15  Biscuit: Medication (not done)

Mochi, still to do:
  flexible  Mochi: Fetch in the yard (not done)
     07:30  Mochi: Morning walk (not done)
     09:15  Mochi: Evening walk (not done)
     07:00  Mochi: Breakfast (not done)

Plan for Jordan on Tuesday, Oct 06 2026 (available 07:00-10:00, 180 min):
  07:00-07:20  Mochi: Fetch in the yard (20 min) [medium] - medium priority, placed in earliest free slot
  07:30-08:00  Mochi: Morning walk (30 min) [high] - fixed at preferred time 07:30
  08:00-08:10  Biscuit: Litter box (10 min) [medium] - moved from preferred time 07:45 to avoid Mochi: Morning walk
  08:10-08:25  Biscuit: Brush coat (15 min) [low] - low priority, placed in earliest free slot
  09:15-09:45  Mochi: Evening walk (30 min) [medium] - fixed at preferred time 09:15
Total: 105 of 180 min used.
Conflicts detected:
  Biscuit: Litter box at 07:45 overlaps Mochi: Morning walk - moved to 08:00
```

The completed *Breakfast* and *Medication* each appear twice in the task lists: once as today's done occurrence and once as tomorrow's new one. Only tasks still due today make it into the plan.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
