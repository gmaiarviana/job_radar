# Project Instructions — Job Radar

This file contains specific rules, patterns, and optimizations discovered during the development of the Job Radar project.

## 1. Environment & Shell
- **OS**: Windows
- **Shell**: PowerShell (use `;` to chain commands, not `&&`).
- **Python**: Use `python` (not `python3`) and ensure the virtual environment `venv` is active.

## 2. Git & Data Flow
- **Pattern**: Data-as-code. GitHub Actions generates data in the cloud and pushes it to the repo.
- **Gitignore Rules**:
    - ✅ **Allowed**: `data/raw/*.json` and `data/scored/*.json` (must be committed for the Streamlit app to work).
    - 🚫 **Ignored**: `data/feedback/` and `data/output/` (contains local feedback and generated PDFs which should NOT be in the repo).
    - 🚫 **Ignored**: Legacy `/*.json` files in the root.

## 3. Career Data Management
- **Source of Truth**: `config/career_narrative.md` (Long, detailed, used for reference).
- **LLM Context**: `config/profile.md` (Condensed, ~800 tokens, structured for the scoring prompt).
- **Instruction**: When updating the profile, always check if the Career Narrative has more relevant details.

## 4. Prompting & LLMs
- **Tone**: Professional, direct, no clichês (especially for cover letters).
- **Model Choice**: 
    - Fetch: OpenAI (web search preview).
    - Score: Claude Haiku (cost-effective scoring).
    - Generate: Claude Sonnet (high-quality writing).

## 5. Development Patterns
## 6. Functionality Closure (Lifecycle)
At the end of every task or feature implementation, ALWAYS perform these steps:
1. **Self-Correction**: Review the chat for any errors, repeated corrections, or environment quirks. Update this `instructions.md` file to prevent recurrence.
2. **Roadmap Sync**: Update `ROADMAP.md`. **Keep future plans detailed and comprehensive** so they serve as a technical guide. Only simplify the "Done" section to keep the document focused on upcoming work; the code/git is the record for what's already completed.
3. **Commit**: Ensure all changes are staged and pushed with a descriptive message.
4. **Cleanup**: Check for root directory clutter. Ensure new scripts go to `src/` and data goes to `data/`.

---
*Last update: Feb 2026*
