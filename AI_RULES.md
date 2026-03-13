# AI RULES — Project: gis-phl
Stack: Python

This file contains project-specific configurations and commands.

**For general coding rules and principles, see:** `rules/BASE_RULES.md`
**For project-specific overrides and context, see:** `rules/PROJECT_SPECIFIC.md`
**For specialized workflows, see:** `rules/skills/`
**For local collaboration posture during active work, also load if present:** `tmp/codex_working_agreement.md`

**NEVER UPDATE THE AI_RULES.MD, PROJECT_SPECIFIC.MD, OR ANY OF THE RULES FILES WITHOUT EXPRESS PERMISSION**

---

## Project Configuration

**Project Name:** gis-phl
**Stack:** Python

---

## Repo-Specific Commands

### Format
ruff format .

### Lint
ruff check .

### Typecheck
mypy .

### Tests
pytest -q

### Build
python -m build

---

## About This File

This file defines project-specific commands and configurations for AI coding assistants.

The full ruleset (coding style, workflow patterns, security guidelines) is managed via a private template system and synced locally. These files are not committed to public repositories to protect proprietary development workflows.

For more information about the AI ruleset system, see `.custom-ruleset-manager/README.md`
