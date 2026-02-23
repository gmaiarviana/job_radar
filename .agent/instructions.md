# Project Instructions — Job Radar

This file contains specific rules, patterns, and optimizations discovered during the development of the Job Radar project.

## 1. Documentation Responsibilities
To maintain context for AI agents and human collaborators:
- **`README.md`**: High-level "what" and "why". Project explanation, user journey, and setup.
- **`ARCHITECTURE.md`**: Technical "how" (current state). Modules, data flow, tech stack, and rationale.
- **`ROADMAP.md`**: Technical "future" (state to be reached). Detailed implementation plans for upcoming work.
- **`.agent/`**: Execution instructions and workflows.

## 2. Process & Lifecycle
- **Roadmap Sync (MANDATORY)**: Update `ROADMAP.md` at the end of EVERY implementation task. Keep future plans detailed as they serve as technical guides for the next steps.
- **Cleanup**: Check for root directory clutter after each feature. Scripts go to `src/`, data to `data/`.
- **Commit**: Stage and push changes with descriptive messages after verifying functionality.

## 3. Environment & Shell
- **OS**: Windows
- **Shell**: PowerShell (use chain commands with `;`, not `&&`).
- **Python**: Use `python` and ensure `venv` is active (`.\venv\Scripts\Activate.ps1`).

## 4. Git & Data Flow
- **Pattern**: Data-as-code.
- **Gitignore Rules**:
    - ✅ **Allowed**: `data/raw/*.json` and `data/scored/*.json`.
    - 🚫 **Ignored**: `data/feedback/`, `data/output/`, and root level `.json`.

## 5. Career Data & LLMs
- **Source of Truth**: `config/career_narrative.md`.
- **LLM Context**: `config/profile.md` (~800 tokens).
- **Tone**: Professional, direct, no clichês.
- **Model Choice**: 
    - Fetch: OpenAI (search preview).
    - Score: Claude Haiku (cost/vloume).
    - Generate: Claude Sonnet (writing quality).

