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

JD_SCORE_TRUNCATE = 3000  # score_single_job: limite no prompt (boilerplate benefits/EEO não agrega)


def load_profile(profile_path):
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Perfil não encontrado em: {profile_path}")
    return path.read_text(encoding="utf-8")

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

def score_single_job(client, job, profile_content):
    """
    Pontua uma única vaga com análise profunda.
    No prompt, jd_full é truncado a JD_SCORE_TRUNCATE chars (boilerplate/EEO não agrega);
    o objeto job armazenado não é alterado.
    """
    # Truncar JD só no payload do prompt (JD_SCORE_TRUNCATE: boilerplate benefits/EEO não agrega ao score)
    job_for_prompt = dict(job)
    jd_full = (job.get("jd_full") or job.get("description") or "")
    if len(jd_full) > JD_SCORE_TRUNCATE:
        job_for_prompt["jd_full"] = jd_full[:JD_SCORE_TRUNCATE]
    if "description" in job_for_prompt:
        del job_for_prompt["description"]  # evita enviar JD completo em outro campo

    system_prompt = f"""
Você é um recrutador técnico sênior. Sua tarefa é fazer um "deep mapping" entre o perfil do candidato e a vaga abaixo.

# PERFIL DO CANDIDATO
{profile_content}

# RUBRICA DE SCORE — aplicar rigorosamente:
- 85–100: O candidato tem experiência DIRETA no domínio central da vaga, em contexto similar (tipo de empresa, nível de ownership, escala). Gap menor seria apenas setor ou tecnologia pontual. Exige evidência concreta no perfil, não inferência.
- 70–84: Skills principais presentes, mas falta UM elemento crítico: domínio específico (ex: PM de produto próprio vs. consultoria/outsourcing), ou seniority equivalente (ex: Principal/Staff sem histórico comprovado nesse nível), ou contexto de empresa (SaaS product company vs. outsourcing). Candidatura viável mas com risco real.
- 50–69: Skills transferíveis claras, mas o GAP está no CORE da vaga. A função exige especialização que o candidato não demonstrou. Aplicação possível, mas improvável de passar triagem de recrutadores experientes.
- 30–49: Skills genéricas de PM/TPM presentes, mas a vaga exige background específico ausente no perfil. Score reflete potencial de longo prazo, não fit atual.
- 0–29: Perfil sem base para a função. Check eliminatórios deveria ter capturado.

# PENALIZAÇÕES OBRIGATÓRIAS — aplicar ANTES de definir o score:
- Experiência predominante em outsourcing/consultoria (não owna roadmap, cliente define produto): limite máximo 75, mesmo com skills fortes.
- Título "Principal", "Staff" ou "Senior" sem histórico comprovado em cargo equivalente: limite máximo 65.
- Gap de domínio no CORE da vaga (security/compliance, customer success, sales ops, hardware/robotics, aerospace, infrastructure de alta escala): limite máximo 60.
- Combinação de 2+ penalizações acima: limite máximo 55.

# INSTRUÇÕES DE ANÁLISE:
1. EVIDÊNCIA DIRETA: Cite qual requisito da vaga tem evidência direta no perfil. Use o formato: "Requisito: [X] | Evidência: [Y]".
2. PRINCIPAL GAP: Identifique o maior risco ou gap desta candidatura. Seja específico.
3. SCORE (0-100): Atribua o score conforme a rubrica acima, aplicando as penalizações obrigatórias quando couberem.
4. JUSTIFICATIVA: Explique por que esse score (e qual faixa da rubrica / penalização aplicada).

# REGRAS CRÍTICAS:
- PROIBIDO usar termos vagos como "alinhado com o perfil", "boa correspondência", "fit cultural". Se o candidato é bom, PROVE com evidência do perfil.
- O score deve refletir a rubrica e as penalizações. Justifique o número exato.

# FORMATO DE SAÍDA (JSON)
Responda APENAS um JSON:
{{
  "title": "{job.get('title')}",
  "score": int,
  "evidence": "texto",
  "main_gap": "texto",
  "justification": "texto",
  "perfect_match": boolean,
  "url": "{job.get('url')}"
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
        return json.loads(content[start_idx:end_idx])

    except Exception as e:
        print(f"[score.py] [ERR] Erro ao pontuar vaga {job.get('title')}: {e}")
        return None

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

    timestamp = datetime.now().strftime("%H%M%S")
    scored_filename = f"{args.date}_{timestamp}.json"
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

        # 2. Scoring profundo (individual) — jd truncado só no prompt
        scored_jobs = []
        if not passed_jobs:
            print("[score.py] [WARN] Nenhuma vaga restou apos os eliminatorios.")
        else:
            print(f"[score.py] -> Iniciando scoring profundo para {len(passed_jobs)} vagas...")
            for i, job in enumerate(passed_jobs):
                print(f"   [{i+1}/{len(passed_jobs)}] Analisando: {job.get('title')}...")
                res = score_single_job(client, job, profile)
                if res:
                    res["company"] = job.get("company", "N/A")
                    res["location"] = job.get("location", "N/A")
                    res["id"] = job.get("id")
                    scored_jobs.append(res)

        top_jobs = [j for j in scored_jobs if j.get("score", 0) >= 70]

        output_data = {
            "scored_at": datetime.now().isoformat(),
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
