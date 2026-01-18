---
event: PostToolUse
tools:
  - Write
  - Edit
match_files:
  - "backend/**/*.py"
  - "frontend/**/*.tsx"
  - "frontend/**/*.ts"
---

# Code Quality Check Hook

## Purpose
Automatically check code quality after writing/editing code files.

## Instructions

After modifying Python or TypeScript files, verify:

### Python (backend)
1. Import order: stdlib → third-party → local
2. Type hints on function parameters and returns
3. Docstrings for public functions
4. No hardcoded secrets or credentials
5. Async/await consistency

### TypeScript (frontend)
1. Proper typing (avoid `any`)
2. React hooks rules compliance
3. No console.log in production code
4. Proper error handling

## Auto-suggestions
If issues are found, suggest fixes but don't auto-apply without confirmation.
