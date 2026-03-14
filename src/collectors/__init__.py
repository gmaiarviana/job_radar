"""
Coletores de vagas por fonte. Cada coletor expõe uma função () -> list[dict]
que retorna jobs brutos para normalização pelo pipeline.
"""

# Fonte única de verdade para filtros por título ligados a PM/TPM.
TITLE_KEYWORDS = [
    "product manager",
    "program manager",
    "project manager",
    "tpm",
    "product analyst",
    "product ops",
    "technical product",
    "delivery manager",
    "strategy and operations",
    "strategy & operations",
]

TITLE_KEYWORDS_LATAM = TITLE_KEYWORDS + [
    "gerente de producto",
    "gerente de produto",
]

from .remotive import collect_remotive
from .openai_search import collect_openai_web_search
from .jobicy import collect_jobicy
from .greenhouse import collect_greenhouse
from .lever import collect_lever
from .ashby import collect_ashby
from .remoteok import collect_remoteok
from .getonboard import collect_getonboard
from .himalayas import collect_himalayas
from .workingnomads import collect_workingnomads
from .jobscollider import collect_jobscollider

__all__ = [
    "collect_remotive",
    "collect_openai_web_search",
    "collect_jobicy",
    "collect_greenhouse",
    "collect_lever",
    "collect_ashby",
    "collect_remoteok",
    "collect_getonboard",
    "collect_himalayas",
    "collect_workingnomads",
    "collect_jobscollider",
    "TITLE_KEYWORDS",
    "TITLE_KEYWORDS_LATAM",
]
