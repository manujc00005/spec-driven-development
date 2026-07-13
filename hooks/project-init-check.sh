#!/bin/bash
# SessionStart hook — warns if specs/CONSTITUTION.md is missing or has unfilled TODOs

CONSTITUTION="specs/CONSTITUTION.md"

# Not an SDD project if specs/ doesn't exist — skip silently
if [ ! -d "specs" ]; then
  exit 0
fi

# CONSTITUTION.md missing
if [ ! -f "$CONSTITUTION" ]; then
  echo '{"systemMessage":"[SDD] specs/CONSTITUTION.md not found. Agents will work without project rules. Run /project-init to set up your project constitution."}'
  exit 0
fi

# Count unfilled TODOs
TODO_COUNT=$(grep -c "TODO:" "$CONSTITUTION" 2>/dev/null)
TODO_COUNT=${TODO_COUNT:-0}

if [ "$TODO_COUNT" -gt 0 ] 2>/dev/null; then
  echo "{\"systemMessage\":\"[SDD] specs/CONSTITUTION.md has $TODO_COUNT unfilled TODO sections. Run /project-init to complete your project setup.\"}"
fi

exit 0
