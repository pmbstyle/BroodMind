# HEARTBEAT - Scheduled Tasks

This file reflects recurring checks and proactive tasks configured in the scheduler.
It is primarily a readable snapshot, not the source of truth.
Keep entries concrete, bounded, and easy to verify.
Scheduler changes may rewrite this file.

## How To Use

- Each task should have a stable ID.
- Define or update schedules through scheduler tools or commands, then use this file to review the current state.
- Say what should run, how often, what output is expected, and whether the user should be notified.
- Prefer writing results to workspace files instead of keeping them only in chat.
- If a task depends on network access, assign an appropriate worker.
- `Daily at HH:MM` uses UTC.
- If nothing is due, return `HEARTBEAT_OK`.

## Task Template

### Example Task
- **ID**: example_task
- **Description**: Brief description of what this task is for
- **Frequency**: Daily at 09:00
- **Notify user**: if_significant
- **Worker**: web_researcher
- **Task**: [Scheduled: example_task] Do the bounded recurring work and save results to an agreed file
- **Last execution**: Never
- **Status**: Disabled

## Tracking

- example_task_last_run: Never
