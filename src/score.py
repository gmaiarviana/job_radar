import os
import json
import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

# Garante projeto na path ao rodar como python src/score.py
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from src.paths import FILTERED_DIR, SCORED_DIR, ensure_dirs

# Carrega variáveis do arquivo .env
load_dotenv()

JD_SCORE_TRUNCATE = 3000  # analyze_job: limite no prompt (boilerplate/EEO não agrega)

# Ceiling por penalty (Épico 5 — rubrica de scoring). 2+ penalties → 55; nenhuma → 100.
CEILING_BY_PENALTY = {
    "domain_gap_core": 60,
    "seniority_gap": 65,
    "outsourcing_context": 75,
}
CEILING_MULTIPLE_PENALTIES = 55
CEILING_NONE = 100


def compute_ceiling(analysis_output):
    """
    Função pura: recebe o output da Chamada 1 (analyze_job) e retorna ceiling + reason.
    Não chama LLM. Testável sem API.
    Lê analysis_output["penalties"] como dict de bools (seniority_gap, outsourcing_context, domain_gap_core).
    Regras: domain_gap_core→60, seniority_gap→65, outsourcing_context→75;
            2+ true→55; nenhum true→100.
    Se penalties não for dict, retorna ceiling 100 (defensivo).
    Retorna {"ceiling": int, "reason": str}.
    """
    penalties = analysis_output.get("penalties") if isinstance(analysis_output, dict) else None
    if not isinstance(penalties, dict):
        return {"ceiling": CEILING_NONE, "reason": "Nenhuma penalty aplicável (penalties ausente ou inválido)."}

    active = [k for k in CEILING_BY_PENALTY if penalties.get(k) is True]

    if not active:
        return {"ceiling": CEILING_NONE, "reason": "Nenhuma penalty aplicável."}
    if len(active) >= 2:
        return {
            "ceiling": CEILING_MULTIPLE_PENALTIES,
            "reason": f"2+ penalties: {', '.join(active)}.",
        }
    p = active[0]
    return {
        "ceiling": CEILING_BY_PENALTY[p],
        "reason": f"1 penalty: {p}.",
    }


def load_profile(profile_path):
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Perfil não encontrado em: {profile_path}")
    return path.read_text(encoding="utf-8")


def analyze_job(client, job, profile_content):
    """
    Chamada 1 do pipeline de scoring: análise estruturada sem score.
    Recebe job + profile e retorna JSON com core_requirements, seniority_comparison,
    penalties (objeto de booleans) e domain_fit. JD truncada a JD_SCORE_TRUNCATE chars no prompt.
    """
    job_for_prompt = dict(job)
    jd_full = (job.get("jd_full") or job.get("description") or "")
    if len(jd_full) > JD_SCORE_TRUNCATE:
        job_for_prompt["jd_full"] = jd_full[:JD_SCORE_TRUNCATE]
    if "description" in job_for_prompt:
        del job_for_prompt["description"]

    system_prompt = f"""
Você é um recrutador técnico. Sua tarefa é analisar a vaga abaixo em relação ao perfil do candidato e retornar uma análise ESTRUTURADA. NÃO atribua score numérico.

# PERFIL DO CANDIDATO
{profile_content}

# REGRAS DA ANÁLISE
1. CORE REQUIREMENTS: Extraia os 3 a 5 requisitos CENTRAIS da JD — os que definem a vaga, não genéricos (ex: "communication skills"). Para cada um:
   - requirement: texto do requisito
   - category: exatamente uma de: seniority | technical | domain | leadership | other
   - evidence: evidência concreta do perfil que atende, ou string vazia se não houver
   - has_evidence: "full" se o perfil atende o requisito com evidência direta e suficiente; "partial" se há evidência relacionada mas insuficiente em escopo, anos ou profundidade (ex: JD pede 5+ anos e candidato tem ~3; ou JD pede domínio específico e candidato tem domínio adjacente); "false" se não há evidência relevante no perfil.
   IMPORTANTE: has_evidence DEVE ser sempre uma string ('full', 'partial' ou 'false'). Nunca retorne booleanos true/false.

2. SENIORITY COMPARISON: Compare explicitamente anos pedidos na JD vs anos do candidato em papéis PM/TPM/tech. Preencha:
   - jd_asks: o que a JD pede (ex: "8+ years", "5-7 years")
   - candidate_has: o que o candidato tem (ex: "~3 years in PM/TPM tech roles")
   - gap: true se há gap de seniority, false caso contrário

3. PENALTIES: Objeto com três chaves booleanas. Responda true apenas quando o critério se aplicar; caso contrário false.
   - seniority_gap: true se a JD pede X+ anos de experiência e o perfil do candidato tem evidência de menos anos em papéis PM/TPM/tech; false caso contrário.
   - outsourcing_context: true se a experiência predominante do candidato é em consultoria/outsourcing (cliente define produto, candidato não tem ownership de roadmap); false se há evidência forte de product company ou o contexto é misto/neutro.
   - domain_gap_core: true se o DOMÍNIO PRIMÁRIO da vaga — o tipo de produto, sistema ou indústria central — não tem evidência direta no perfil. Avalie o domínio da vaga, não skills genéricos. Ex.: vaga sobre "self-service AI platforms" e candidato com "GenAI PoCs para relatórios" = domínios diferentes; vaga sobre "robotics data collection" e candidato com "program management em SaaS" = domínios diferentes. Pergunte-se: o candidato já construiu, gerenciou ou operou ESTE TIPO de produto ou sistema? Se não, true. Caso contrário false.

4. DOMAIN_FIT: Uma string com valor "full", "partial" ou "none" seguido de " — " e uma breve justificativa (ex: "partial — PM em fintech, vaga é B2B SaaS; skills transferíveis").

# PROIBIÇÕES
- NÃO inclua campo "score" nem qualquer pontuação numérica.
- Responda APENAS um JSON válido, sem texto antes ou depois.

# FORMATO DE SAÍDA (JSON)
{{
  "core_requirements": [
    {{"requirement": "...", "category": "seniority|technical|domain|leadership|other", "evidence": "...", "has_evidence": "full|partial|false"}}
  ],
  "seniority_comparison": {{
    "jd_asks": "...",
    "candidate_has": "...",
    "gap": true
  }},
  "penalties": {{
    "seniority_gap": true,
    "outsourcing_context": false,
    "domain_gap_core": false
  }},
  "domain_fit": "full|partial|none — breve justificativa"
}}
"""

    user_content = f"Vaga para análise:\n{json.dumps(job_for_prompt, indent=2, ensure_ascii=False)}"

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}]
        )
        content = response.content[0].text
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1
        result = json.loads(content[start_idx:end_idx])
        # Normalizar has_evidence: bool → string
        for req in result.get("core_requirements", []):
            he = req.get("has_evidence")
            if he is True:
                req["has_evidence"] = "full"
            elif he is False:
                req["has_evidence"] = "false"
        return result
    except Exception as e:
        print(f"[score.py] [ERR] Erro em analyze_job para {job.get('title')}: {e}")
        return None


def score_with_analysis(client, job, analysis, ceiling_result, profile_content):
    """
    Chamada 2 do pipeline de scoring (Épico 5.1.3).
    Recebe análise (Chamada 1) e ceiling_result (compute_ceiling). Se ceiling ≤ 50, retorna
    sem chamar LLM. Caso contrário, chama Haiku para atribuir score ≤ ceiling.
    Retorna dict com score, score_ceiling, ceiling_reason, justification, main_gap; ou None em erro.
    """
    ceiling = ceiling_result.get("ceiling", 100)
    reason = ceiling_result.get("reason", "")

    if ceiling <= 50:
        return {
            "score": ceiling,
            "score_ceiling": ceiling,
            "ceiling_reason": reason,
            "justification": "Auto-eliminated: penalty ceiling too low",
            "main_gap": analysis.get("domain_fit", ""),
        }

    analysis_json = json.dumps(analysis, indent=2, ensure_ascii=False)
    system_prompt = f"""
Você é um recrutador técnico sênior. Sua tarefa é atribuir um score (0-100) para a candidatura com base na análise já feita.

# PERFIL DO CANDIDATO
{profile_content}

# ANÁLISE DA VAGA (Chamada 1 — já realizada)
{analysis_json}

# RESTRIÇÃO OBRIGATÓRIA
O score MÁXIMO permitido para esta vaga é {ceiling} porque: {reason}. Você DEVE atribuir um score ≤ {ceiling}.

# RUBRICA DE FAIXAS (escolha a faixa que melhor descreve o fit; o score final deve ser ≤ {ceiling})
- 85–100: Experiência DIRETA no domínio central, contexto similar. Evidência concreta no perfil.
- 70–84: Skills principais presentes, falta UM elemento crítico (domínio, seniority ou contexto). Candidatura viável com risco.
- 50–69: Skills transferíveis, mas GAP no CORE da vaga. Improvável passar triagem experiente.
- 30–49: Skills genéricas de PM/TPM; vaga exige background específico ausente. Potencial de longo prazo.
- 0–29: Perfil sem base para a função.

# INSTRUÇÕES
1. Atribua um score inteiro entre 0 e {ceiling} (inclusive).
2. Justifique brevemente o score e a faixa aplicada.
3. main_gap: o principal gap ou risco desta candidatura (uma frase).

Responda APENAS um JSON válido, sem texto antes ou depois.

# FORMATO DE SAÍDA (JSON)
{{
  "score": int,
  "score_ceiling": {ceiling},
  "ceiling_reason": "texto (motivo do teto)",
  "justification": "texto",
  "main_gap": "texto"
}}
"""

    user_content = f"Atribua score para a vaga: {job.get('title', 'N/A')} (empresa: {job.get('company', 'N/A')})."

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        content = response.content[0].text
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1
        if start_idx < 0 or end_idx <= start_idx:
            print(f"[score.py] [ERR] score_with_analysis: JSON não encontrado na resposta.")
            return None
        out = json.loads(content[start_idx:end_idx])
        # Garantir os 5 campos no retorno
        out["score_ceiling"] = ceiling
        out["ceiling_reason"] = reason
        return out
    except Exception as e:
        print(f"[score.py] [ERR] Erro em score_with_analysis para {job.get('title')}: {e}")
        return None


def check_eliminatorios(client, jobs, profile_content):
    """
    Filtra vagas em batch usando Claude Haiku para critérios eliminatórios.
    Envia title, company, location e jd_full (descrição completa) para análise.
    Retorna (passed_jobs, eliminated_jobs) — objetos job completos, mapeados por title.
    """
    if not jobs:
        return [], []

    # Objeto por vaga: title, company, location e jd_full (completo) para o LLM
    reduced = []
    for j in jobs:
        jd_full = (j.get("jd_full") or j.get("description") or "")
        reduced.append({
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "location": j.get("location", ""),
            "jd_full": jd_full,
        })

    system_prompt = f"""
Você é um recrutador técnico. Analise a lista de vagas abaixo e verifique se atendem aos critérios eliminatórios do candidato.
Cada vaga inclui a descrição completa (jd_full) da posição para você avaliar.

# PERFIL DO CANDIDATO (CRITÉRIOS)
{profile_content}

# CRITÉRIOS ELIMINATÓRIOS:
1. Localização (LOCATION): O candidato é brasileiro, trabalha remotamente do Brasil, SEM autorização de trabalho em US, Canada, UK, EU ou Austrália.
   - ELIMINAR se a vaga exigir: residência, work authorization ou presença física em US, Canada, UK, EU, Austrália ou Israel.
   - PERMITIR se for: worldwide, global, LATAM, ou países onde brasileiro pode trabalhar remotamente (Brazil, Mexico, Colombia, Argentina, Chile, etc.).
   - PERMITIR se location estiver vazia ou ambígua — em caso de dúvida, beneficie o candidato.
2. Nível: Sênior, Staff, Principal ou Lead apenas. (Junior, Pleno, Mid, Estágio = ELIMINADO)
3. Tipo de Cargo: PM, TPM ou Híbrido PM/Tech. (Engenheiro puro, EM, Marketing puro = ELIMINADO)
4. Idioma: Vaga deve ser em Inglês (vagas apenas em PT ou ES = ELIMINADO)

# FORMATO DE SAÍDA (JSON)
Retorne APENAS um objeto JSON com:
- "results": lista de objetos contendo:
    - "title": título original
    - "status": "passa" ou "eliminada"
    - "reason": se eliminada, qual o motivo (localização, nível, tipo de cargo, idioma). Se passa, deixe vazio.

Responda APENAS o JSON.
"""

    user_content = "Avalie as seguintes vagas:\n" + json.dumps(reduced, indent=2, ensure_ascii=False)

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}]
        )
        
        content = response.content[0].text
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1
        data = json.loads(content[start_idx:end_idx])
        results = data.get("results", [])

        passed = []
        eliminated = []
        job_map = {j["title"]: j for j in jobs}

        for res in results:
            title = res.get("title")
            job = job_map.get(title)
            if job:
                if res.get("status") == "passa":
                    passed.append(job)
                else:
                    job_copy = job.copy()
                    job_copy["filter_reason"] = res.get("reason", "eliminado LLM")
                    eliminated.append(job_copy)
            
        return passed, eliminated

    except Exception as e:
        print(f"[score.py] [ERR] Erro em check_eliminatorios: {e}")
        return jobs, [] # Fallback: passa tudo para o scoring individual se falhar o batch


def main():
    parser = argparse.ArgumentParser(description="Pontua vagas via Claude Haiku")
    parser.add_argument("--date", default=str(date.today()), help="Data no formato YYYY-MM-DD")
    args = parser.parse_args()

    ensure_dirs()

    # Input: ler de FILTERED_DIR por padrão (pipeline: fetch → filter → score)
    # Aceita YYYY-MM-DD*.json ou seed_YYYY-MM-DD_*.json; usa o mais recente por mtime
    filtered_dir = FILTERED_DIR
    filtered_files = sorted(
        (f for f in filtered_dir.glob(f"*{args.date}*.json") if not f.name.startswith("seed_")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not filtered_files:
        print(f"[score.py] [ERR] Nenhum arquivo encontrado em {filtered_dir} para a data: {args.date}")
        print("[score.py] Execute filter.py após fetch.py.")
        return

    filtered_path = filtered_files[0]

    run_time = datetime.now().astimezone()
    scored_filename = f"{run_time:%Y-%m-%d_%H%M%S}.json"
    scored_path = SCORED_DIR / scored_filename
    scored_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[score.py] Pontuando vagas de {filtered_path.name}...")

    try:
        filtered_data = json.loads(filtered_path.read_text(encoding="utf-8"))
        jobs = filtered_data.get("jobs", [])

        if not jobs:
            print("[score.py] [WARN] Nenhuma vaga encontrada no arquivo filtered.")
            return

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("[score.py] [ERR] Erro: ANTHROPIC_API_KEY nao encontrada.")
            return

        client = Anthropic(api_key=api_key)
        profile = load_profile("config/profile.md")

        # 1. Eliminatórios (Batch LLM) — prompt usa jd_full por vaga
        print(f"[score.py] -> Verificando eliminatórios para {len(jobs)} vagas...")
        passed_jobs, llm_eliminated = check_eliminatorios(client, jobs, profile)
        print(f"[score.py] [i] Vagas eliminadas pelo LLM: {len(llm_eliminated)}")

        # 2. Pipeline de 2 chamadas: analyze_job → compute_ceiling → score_with_analysis
        scored_jobs = []
        if not passed_jobs:
            print("[score.py] [WARN] Nenhuma vaga restou apos os eliminatorios.")
        else:
            print(f"[score.py] -> Iniciando scoring profundo (2 chamadas) para {len(passed_jobs)} vagas...")
            for i, job in enumerate(passed_jobs):
                analysis = analyze_job(client, job, profile)
                if analysis is None:
                    continue
                ceiling_result = compute_ceiling(analysis)
                result = score_with_analysis(client, job, analysis, ceiling_result, profile)
                if result is None:
                    continue
                result["company"] = job.get("company", "N/A")
                result["location"] = job.get("location", "N/A")
                result["title"] = job.get("title", "")
                result["url"] = job.get("url", "")
                result["id"] = job.get("id")
                result["core_requirements"] = analysis.get("core_requirements", [])
                result["seniority_comparison"] = analysis.get("seniority_comparison", {})
                scored_jobs.append(result)
                ceiling = ceiling_result.get("ceiling", 0)
                score = result.get("score", 0)
                print(f"   [{i+1}/{len(passed_jobs)}] Analisando: {result.get('title', '')}... ceiling={ceiling} score={score}")

        top_jobs = [j for j in scored_jobs if j.get("score", 0) >= 70]

        output_data = {
            "scored_at": run_time.isoformat(),
            "source_file": filtered_path.name,
            "summary": {
                "total_input": len(jobs),
                "total_llm_eliminated": len(llm_eliminated),
                "total_scored": len(scored_jobs),
                "total_top": len(top_jobs)
            },
            "jobs": top_jobs,
            "scored_jobs": scored_jobs,
            "eliminated_jobs": llm_eliminated
        }

        scored_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[score.py] [OK] Sucesso! {len(scored_jobs)} vagas pontuadas salvas em {scored_path}")

    except Exception as e:
        print(f"[score.py] [ERR] Ocorreu um erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
