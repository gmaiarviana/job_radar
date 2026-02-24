"""
Coletores de vagas por fonte. Cada coletor expõe uma função () -> list[dict]
que retorna jobs brutos para normalização pelo pipeline.
"""

from .remotive import collect_remotive
from .openai_search import collect_openai_web_search

__all__ = ["collect_remotive", "collect_openai_web_search"]
