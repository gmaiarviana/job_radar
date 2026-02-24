"""
Coletor OpenAI gpt-4o-mini com web search. Retorna jobs brutos para normalização.
"""

import json
from openai import OpenAI

LOG_PREFIX = "[fetch]"


def collect_openai_web_search(
    client: OpenAI,
    roles: list,
    locations: list,
    lookback_hours: int,
) -> list[dict]:
    """
    Coletor: OpenAI gpt-4o-mini com web search.
    Retorna lista de jobs brutos (dict) para normalização.
    """
    roles_str = ", ".join(roles)
    locs_str = ", ".join(locations)

    prompt = f"""
    Busque de 5 a 10 vagas de emprego REAIS para os cargos solicitados.
    FOCO: Vagas publicadas recentemente (últimos 14 dias).

    CRITÉRIOS DE BUSCA:
    - Cargos: {roles_str}
    - Localização: {locs_str} (Priorize 'Remote LATAM' ou 'Remote Worldwide')

    REGRAS DE QUALIDADE (OBRIGATÓRIO):
    1. FONTE E LINK: Para cada vaga, forneça a 'source' (ex: LinkedIn, Greenhouse, Site da Empresa) e o link direto.
    2. PRIORIDADE DE LINK: Dê preferência absoluta para links de sistemas de rastreamento de candidatos (ATS) como greenhouse.io, lever.co, workday.com ou o portal de carreiras oficial da empresa.
    3. EVITE TERCEIROS: Não inclua vagas de sites agregadores suspeitos ou links que pareçam quebrados/antigos.
    4. RECÊNCIA: Priorize o que foi postado recentemente.
    5. EXTRAÇÃO DE LOCALIZAÇÃO (CRÍTICO): Extraia a localização EXATAMENTE como descrita no JD.
       Use frases literais se encontradas (ex: "based in EMEA", "United States only", "open to LATAM", "Remote Worldwide").
       NÃO INFERA localização pelo contexto da busca. Se o JD diz "United States", coloque "United States", mesmo que a busca tenha sido por "Remote Worldwide".

    REGRAS DE OUTPUT (JSON):
    - "title": Título da vaga
    - "company": Empresa
    - "source": Onde a vaga foi encontrada (ex: 'LinkedIn', 'Página de Carreira')
    - "salary": Faixa salarial se mencionada (adicione valor MENSAL se possível ou anual), caso contrário null
    - "location": Localização literal do JD (ex: 'EMEA only', 'United States')
    - "location_confidence": "high" se a localização está explícita no JD, "low" se for ambígua ou ausente.
    - "url": Link DIRETAMENTE para a candidatura ou postagem oficial
    - "requirements": Resumo de 1-2 sentenças
    - "date": Tempo desde a publicação (ex: '2 days ago')

    Retorne APENAS o JSON sob a chave "jobs".
    """

    print(f"{LOG_PREFIX} 📡 Coletor openai_web_search: buscando para {roles_str}...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini-search-preview",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um especialista em busca de vagas remotas. Use sua capacidade de busca web para encontrar informações reais e atuais.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)
        return data.get("jobs", [])

    except Exception as e:
        print(f"{LOG_PREFIX} ✗ Erro no coletor openai_web_search: {e}")
        return []
