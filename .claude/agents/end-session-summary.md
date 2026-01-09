# End Session Summary Agent

## Purpose
Automatically generates a comprehensive session summary documenting all changes, fixes, decisions, and errors resolved during a development session.

## When to Use
Run this agent at the end of each development session to create a permanent record of what was accomplished.

## Usage
```bash
# In Claude Code CLI
/run end-session-summary
```

## What This Agent Does

### 1. Analyzes Git Changes
- Reviews all uncommitted and committed changes in the session
- Identifies modified, added, and deleted files
- Extracts key code changes

### 2. Documents Errors Fixed
- Lists all error messages encountered
- Documents root causes identified
- Records solutions applied
- Notes any workarounds implemented

### 3. Records Decisions Made
- Architecture decisions (e.g., "Used Docker instead of manual setup")
- Technology choices (e.g., "Chose MongoDB over PostgreSQL")
- Configuration decisions (e.g., "Removed volume mount to fix container exit")
- Code structure decisions (e.g., "Fixed class method indentation")

### 4. Tracks Progress
- Lists completed features
- Notes partially completed work
- Identifies pending tasks
- Documents known issues

### 5. Generates Output Files

Creates the following in `.claude/sessions/`:
- `session-YYYY-MM-DD-HHMMSS.md` - Main summary
- `errors-fixed.json` - Structured error log
- `decisions.json` - Decision log
- `changes.diff` - Git diff of all changes

## Output Format

```markdown
# Development Session Summary
**Date**: YYYY-MM-DD HH:MM:SS
**Duration**: X hours Y minutes

## Session Objective
[What was the main goal]

## Accomplishments
- [Feature 1 completed]
- [Bug 2 fixed]
- [Configuration 3 updated]

## Errors Encountered and Fixed

### Error 1: [Error Name]
**Error Message**:
```
[Full error message]
```

**Root Cause**: [Explanation]

**Solution**: [How it was fixed]

**Files Modified**:
- [file1.py:123]
- [file2.js:456]

---

## Technical Decisions Made

### Decision 1: [Decision Title]
**Context**: [Why this decision was needed]

**Options Considered**:
1. Option A - [pros/cons]
2. Option B - [pros/cons]

**Decision**: [What was chosen]

**Rationale**: [Why this option]

**Impact**: [What this affects]

---

## Code Changes Summary

### Backend Changes
- **server.py**: Fixed indentation issues in `_calculate_contributions` method
- **Dockerfile**: Added system dependencies for scientific packages

### Frontend Changes
- **public/index.html**: Removed Emergent AI branding
- **Dockerfile**: Added `--force` flag for npm install

### Infrastructure Changes
- **docker-compose.yml**: Removed backend volume mount
- **.env files**: Created environment configuration files

## Files Modified
[List of all files with line counts]

## Next Steps
1. [Task 1 to do in next session]
2. [Task 2 to do in next session]

## Known Issues
- [Issue 1 description]
- [Issue 2 description]

## Notes
[Any additional context or observations]
```

## Configuration

Edit `.claude/agents/config/end-session-summary.json`:

```json
{
  "output_directory": ".claude/sessions",
  "include_git_diff": true,
  "include_error_logs": true,
  "include_decisions": true,
  "auto_commit_summary": false,
  "summary_format": "markdown",
  "generate_json_logs": true
}
```

## Agent Behavior

1. **Scans recent activity** - Reviews last N hours of changes
2. **Extracts context** - Uses AI to understand what was being worked on
3. **Categorizes changes** - Groups by type (bugfix, feature, config, etc.)
4. **Formats output** - Generates clean, readable documentation
5. **Saves artifacts** - Creates timestamped files in sessions folder

## Example Session Summary

See `.claude/sessions/example-session.md` for a complete example of agent output.

## Tips

- Run this agent BEFORE ending your session
- Review the generated summary for accuracy
- Add any manual notes to the summary file after generation
- Commit the session summary to git for permanent record
- Use session summaries to create changelog entries
