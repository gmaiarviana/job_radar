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

from src.score import compute_ceiling, score_with_analysis


def test_compute_ceiling():
    """4 cenários: nenhuma penalty → 100; domain_gap_core → 60; 2 penalties → 55; 3 penalties → 55. Formato: penalties como dict de bools."""
    # Cenário 1: nenhuma penalty → 100
    out = compute_ceiling({
        "penalties": {"seniority_gap": False, "outsourcing_context": False, "domain_gap_core": False}
    })
    assert out["ceiling"] == 100, out
    assert "reason" in out, out

    # Cenário 2: 1 penalty (domain_gap_core) → 60
    out = compute_ceiling({
        "penalties": {"seniority_gap": False, "outsourcing_context": False, "domain_gap_core": True}
    })
    assert out["ceiling"] == 60, out
    assert "domain_gap_core" in out["reason"], out

    # Cenário 3: 2 penalties → 55
    out = compute_ceiling({
        "penalties": {"seniority_gap": True, "outsourcing_context": True, "domain_gap_core": False}
    })
    assert out["ceiling"] == 55, out
    assert "2+" in out["reason"], out

    # Cenário 4: 3 penalties → 55
    out = compute_ceiling({
        "penalties": {"seniority_gap": True, "outsourcing_context": True, "domain_gap_core": True}
    })
    assert out["ceiling"] == 55, out
    assert "2+" in out["reason"], out


def test_score_with_analysis_auto_eliminate():
    """Ceiling ≤ 50: não chama LLM; retorna score=ceiling e justification contém 'Auto-eliminated'."""
    analysis = {"domain_fit": "partial — gap em domínio"}
    ceiling_result = {"ceiling": 50, "reason": "1 penalty: domain_gap_core."}
    out = score_with_analysis(None, {"title": "Test"}, analysis, ceiling_result, "Profile")
    assert out is not None, "score_with_analysis deve retornar dict no early return"
    assert out["score"] == 50, out
    assert out["score_ceiling"] == 50, out
    assert out["ceiling_reason"] == ceiling_result["reason"], out
    assert "Auto-eliminated" in out["justification"], out
    assert out["main_gap"] == analysis["domain_fit"], out


def test_score_with_analysis_auto_eliminate_ceiling_45():
    """Ceiling=45: mesmo early return, score=45."""
    analysis = {"domain_fit": "none — core gap"}
    ceiling_result = {"ceiling": 45, "reason": "2+ penalties."}
    out = score_with_analysis(None, {"title": "Test"}, analysis, ceiling_result, "Profile")
    assert out is not None, out
    assert out["score"] == 45, out
    assert out["score_ceiling"] == 45, out
    assert "Auto-eliminated" in out["justification"], out


if __name__ == "__main__":
    test_compute_ceiling()
    test_score_with_analysis_auto_eliminate()
    test_score_with_analysis_auto_eliminate_ceiling_45()
    print("[test_scoring.py] compute_ceiling: 4 cenários OK; score_with_analysis auto-eliminate: 2 cenários OK.")
