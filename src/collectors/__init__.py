"""
Coletores de vagas por fonte. Cada coletor expõe uma função () -> list[dict]
que retorna jobs brutos para normalização pelo pipeline.
"""

from .remotive import collect_remotive
from .openai_search import collect_openai_web_search
from .weworkremotely import collect_weworkremotely
from .jobicy import collect_jobicy
from .greenhouse import collect_greenhouse
from .lever import collect_lever
from .ashby import collect_ashby

__all__ = ["collect_remotive", "collect_openai_web_search", "collect_weworkremotely", "collect_jobicy", "collect_greenhouse", "collect_lever", "collect_ashby"]
