"""Convert data/raw and data/scored JSONs to TXT in their copy txt/ folders (for NotebookLM)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAIRS = [
    (ROOT / "data" / "raw", ROOT / "data" / "raw" / "copy txt"),
    (ROOT / "data" / "scored", ROOT / "data" / "scored" / "copy txt"),
]

for src_dir, out_dir in PAIRS:
    if not src_dir.is_dir():
        continue
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in src_dir.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            txt_path = out_dir / (p.stem + ".txt")
            txt_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(txt_path.relative_to(ROOT))
        except Exception as e:
            print(p.name, "->", e)
