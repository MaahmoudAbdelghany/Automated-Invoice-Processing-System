# Workspace Rules

## 1. Session Memory & Plan Persistence
- **Plan Location & Persistence**: Keep both `implementation_plan.md` and `TASK_PLAN.md` saved directly in the workspace root directory.
- **Plan Verification**: Always read `implementation_plan.md` and `TASK_PLAN.md` by explicit file path from the workspace root (using `view_file`) before starting work or resuming execution.
- **Task Tracking**: After completing each step, update `TASK_PLAN.md` with completed checkboxes `- [x]` and commit the file.

## 2. Step-by-Step Task Execution & GitHub Sync
- **One Step at a Time**: Execute only one step of a task plan in a turn.
- **Explain Progress**: After completing each step, explain clearly what was done and why.
- **Commit & Push**: Commit all changes for that step and push them to the GitHub repository.
- **Wait for Approval**: Stop and ask the user for explicit permission/approval ("go ahead") before moving to the next step. Do NOT proceed without explicit user approval.
