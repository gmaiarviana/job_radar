"""
Testes de scoring (compute_ceiling) — sem dependência de pytest.
Rodar: python src/eval/test_scoring.py
"""
import sys
from pathlib import Path

# Garante projeto na path ao rodar como python src/eval/test_scoring.py
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from src.score import compute_ceiling


def test_compute_ceiling():
    """4 cenários: nenhuma penalty → 100; domain_gap_core → 60; 2 penalties → 55; 3 penalties → 55."""
    # Cenário 1: nenhuma penalty → 100
    out = compute_ceiling({"applicable_penalties": []})
    assert out["ceiling"] == 100, out
    assert "reason" in out, out

    # Cenário 2: 1 penalty (domain_gap_core) → 60
    out = compute_ceiling({"applicable_penalties": ["domain_gap_core"]})
    assert out["ceiling"] == 60, out
    assert "domain_gap_core" in out["reason"], out

    # Cenário 3: 2 penalties → 55
    out = compute_ceiling({"applicable_penalties": ["seniority_gap", "outsourcing_context"]})
    assert out["ceiling"] == 55, out
    assert "2+" in out["reason"], out

    # Cenário 4: 3 penalties → 55
    out = compute_ceiling({
        "applicable_penalties": ["domain_gap_core", "seniority_gap", "outsourcing_context"]
    })
    assert out["ceiling"] == 55, out
    assert "2+" in out["reason"], out


if __name__ == "__main__":
    test_compute_ceiling()
    print("[test_scoring.py] compute_ceiling: 4 cenários OK.")
