import os
import json
import argparse
from datetime import date, datetime
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

# Carrega variáveis do arquivo .env
load_dotenv()

JD_SNIPPET_LENGTH = 300   # check_eliminatorios: primeiros N chars do JD no prompt
JD_SCORE_TRUNCATE = 3000  # score_single_job: limite no prompt (boilerplate benefits/EEO não agrega)


def load_profile(profile_path):
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Perfil não encontrado em: {profile_path}")
    return path.read_text(encoding="utf-8")

def check_eliminatorios(client, jobs, profile_content):
    """
    Filtra vagas em batch usando Claude Haiku para critérios eliminatórios.
    Envia apenas title, company, location e jd_snippet (300 chars) para reduzir tokens.
    Retorna (passed_jobs, eliminated_jobs) — objetos job completos, mapeados por title.
    """
    if not jobs:
        return [], []

    # Objeto reduzido por vaga: só o necessário para eliminatórios (jd_full não vai no prompt)
    reduced = []
    for j in jobs:
        jd_full = (j.get("jd_full") or j.get("description") or "")
        jd_snippet = jd_full[:JD_SNIPPET_LENGTH] if jd_full else ""
        reduced.append({
            "title": j.get("title", ""),
            "company": j.get("company", ""),
            "location": j.get("location", ""),
            "jd_snippet": jd_snippet,
        })

    system_prompt = f"""
Você é um recrutador técnico. Analise a lista de vagas abaixo e verifique se atendem aos critérios eliminatórios do candidato.

# PERFIL DO CANDIDATO (CRITÉRIOS)
{profile_content}

# CRITÉRIOS ELIMINATÓRIOS:
1. Localização: Apenas Remote LATAM ou Remote Worldwide. (US-only, EU-only, etc = ELIMINADO)
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
        print(f"[score.py] ✗ Erro em check_eliminatorios: {e}")
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

# INSTRUÇÕES DE ANÁLISE:
1. EVIDÊNCIA DIRETA: Cite qual requisito da vaga tem evidência direta no perfil. Use o formato: "Requisito: [X] | Evidência: [Y]".
2. PRINCIPAL GAP: Identifique o maior risco ou gap desta candidatura. Seja específico.
3. SCORE (0-95): Atribua um score de 0 a 95. SCORE 100 É PROIBIDO.
4. JUSTIFICATIVA: Explique por que esse score e não 10 pontos acima ou abaixo. 

# REGRAS CRÍTICAS:
- PROIBIDO usar termos como "alinhado com o perfil", "boa correspondência", "fit cultural", "perfil adequado", "se alinha bem", "atende aos requisitos".
- Se você quiser dizer que o candidato é bom, PROVE com uma evidência do perfil (ex: "O candidato já liderou projetos de X, o que é idêntico ao pedido em Y").
- SCORE 100 É TERMINANTEMENTE PROIBIDO. Máximo 95.
- O score deve ser conservador. Justifique o número exato (ex: "90 e não 80 porque X, mas não 95 porque falta Y").

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
        print(f"[score.py] ✗ Erro ao pontuar vaga {job.get('title')}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Pontua vagas via Claude Haiku")
    parser.add_argument("--date", default=str(date.today()), help="Data no formato YYYY-MM-DD")
    args = parser.parse_args()

    # Input: ler de data/filtered/ por padrão (pipeline: fetch → filter → score)
    filtered_dir = Path("data/filtered")
    filtered_files = sorted(filtered_dir.glob(f"{args.date}*.json"), reverse=True)

    if not filtered_files:
        print(f"[score.py] ❌ Nenhum arquivo encontrado em data/filtered/ para a data: {args.date}")
        print("[score.py] Execute filter.py após fetch.py.")
        return

    filtered_path = filtered_files[0]

    timestamp = datetime.now().strftime("%H%M%S")
    scored_filename = f"{args.date}_{timestamp}.json"
    scored_path = Path("data/scored") / scored_filename
    scored_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[score.py] Pontuando vagas de {filtered_path.name}...")

    try:
        filtered_data = json.loads(filtered_path.read_text(encoding="utf-8"))
        jobs = filtered_data.get("jobs", [])

        if not jobs:
            print("[score.py] ⚠️ Nenhuma vaga encontrada no arquivo filtered.")
            return

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("[score.py] ✗ Erro: ANTHROPIC_API_KEY não encontrada.")
            return

        client = Anthropic(api_key=api_key)
        profile = load_profile("config/profile.md")

        # 1. Eliminatórios (Batch LLM) — prompt usa apenas snippet por vaga
        print(f"[score.py] -> Verificando eliminatórios para {len(jobs)} vagas...")
        passed_jobs, llm_eliminated = check_eliminatorios(client, jobs, profile)
        print(f"[score.py] ℹ️ Vagas eliminadas pelo LLM: {len(llm_eliminated)}")

        # 2. Scoring profundo (individual) — jd truncado só no prompt
        scored_jobs = []
        if not passed_jobs:
            print("[score.py] ⚠️ Nenhuma vaga restou após os eliminatórios.")
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

        top_jobs = [j for j in scored_jobs if j.get("score", 0) >= 80]

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
            "eliminated_jobs": llm_eliminated
        }

        scored_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[score.py] ✅ Sucesso! {len(scored_jobs)} vagas pontuadas salvas em {scored_path}")

    except Exception as e:
        print(f"[score.py] ✗ Ocorreu um erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
