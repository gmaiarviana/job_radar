---
description: how to commit and push changes on this project (Windows PowerShell)
---

// turbo-all

> ⚠️ This project runs on **Windows PowerShell**. Use `;` to chain commands, NOT `&&` (which is invalid in PowerShell).

1. Check current git status:
```powershell
git status
```

2. Stage only relevant changes:
```powershell
git add <file1> <file2> ...
```

3. Commit with a descriptive message:
```powershell
git commit -m "<message>"
```

4. Push to remote:
```powershell
git push
```
