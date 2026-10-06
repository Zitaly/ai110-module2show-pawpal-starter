# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

There's user, pet, and task. The user can add, remove, and update pets. Pets have add and remove task. Tasks have update task. the user would have perform all actions, but each action is under a different interface.

The design evolved to have Owner, Pet, Task, and Schedule. Owner owned Pet and planned Schedule. It could add and remove pet, see all tasks, and create scheduling. Pet needed a Task. It could add and remove a task and see pending tasks. Schedule ordered Tasks. It could have a list of tasks, see conflicts, and explain the schedule. Task can mark complete, rank priority, and see when a task is due.
**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

There were numerous changes that had to be made. This is one. In the initial design, Tasks did not know which pet it belonged to. To fix this, Task was given a field for the pet's name, which will allow the task to be traced back to the pet it's for.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler prioritizes readability and ease of debugging.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

With the prioritization of readability and debugging, the scheduler can't create the best possible plan. This is fine, as certain pets and actions may have set schedules that can't be optimized. This can be left to the owner's disgression.
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

AI was used for coding and drafting up plans. The most helpful prompts were theones that ensured the AI would always ask for input before moving forward.
**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
There were a few times where the AI wanted to continue changes after the file was already changed, so I rejected those.

When I evaluate AI suggestions, I look at the justification used, the relevance to what I want, and what's being written.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I primarily tested the core behaviors of the app, as these were crucial to the app's functionality. Bugs with them meant that the core of the app wouldn't work.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm mildly confident that the scheduler works correctly. It's still AI-generated code. I can't think of any edge cases.
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm satisfied with the ability of AI to quickly build larger systems. Without it, a project like this would have taken weeks or months, especially with the backend logic.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would have more of a concrete and detailed plan. I think the AI would work better that way.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

AI needs to be kept on a tight leash, and code needs to be looked at and tested after every change when possible.