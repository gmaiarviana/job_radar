---
description: how to verify the fetch-score-generate pipeline stubs
---

// turbo-all

> ⚠️ This project runs on **Windows PowerShell**.

1. Run the full pipeline stubs to check for syntax errors and directory creation:
```powershell
python src/fetch.py; python src/score.py; python src/generate.py --job-id 123; python src/notify.py
```

2. Check if the output directories exist (Note: stubs may not create JSON files yet):
```powershell
ls data/raw; ls data/scored; ls data/feedback; ls data/output
```

3. Verify Python dependencies (optional):
```powershell
pip check
```
