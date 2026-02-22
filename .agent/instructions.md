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
- **Stubs**: Python stubs in `src/` are placeholders. To verify the full pipeline (fetch -> score -> generate), the scripts must actually write JSON files to the expected `data/` subdirectories. Output error messages if dependency files are missing.
