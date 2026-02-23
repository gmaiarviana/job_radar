import os
import json
import argparse
from datetime import date, datetime
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

# Carrega variáveis do arquivo .env
load_dotenv()

def load_profile(profile_path):
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Perfil não encontrado em: {profile_path}")
    return path.read_text(encoding="utf-8")

def score_jobs(client, jobs, profile_content):
    """
    Pontua uma lista de vagas usando Claude Haiku.
    """
    if not jobs:
        return []

    system_prompt = f"""
Você é um recrutador técnico especialista em Product Management e Technical Program Management.
Sua tarefa é avaliar vagas de emprego para um candidato específico com base no perfil fornecido abaixo.

# PERFIL DO CANDIDATO
{profile_content}

# INSTRUÇÕES DE SCORING
Avali cada vaga em uma escala de 0 a 100 baseada nos seguintes pesos:
1. **Localização (ELIMINATÓRIO):** Se não for 'Remote LATAM' ou 'Remote Worldwide', score = 0.
2. **Nível (ELIMINATÓRIO):** Se for Junior, Pleno sem senioridade ou Estágio, score = 0.
3. **Salário (PESO ALTO):** Alvo >= $5.500 USD/mês. Penalize se for menor ou se não estiver listado.
4. **Fit de Cargo (PESO ALTO):** PM, TPM ou Híbrido.
5. **Idioma:** Inglês é o idioma alvo para o mercado internacional.

# FORMATO DE SAÍDA (JSON)
Retorne APENAS um objeto JSON com a chave "scored_jobs", que é uma lista de objetos:
- "title": (string) o título original da vaga
- "score": (int) 0-100
- "justification": (string) uma única linha explicando o score
- "perfect_match": (boolean) true se score >= 95
- "url": (string) o link original da vaga

Seja rigoroso. Apenas vagas realmente alinhadas devem ter score > 80.
    """

    user_content = "Avalie as seguintes vagas:\n" + json.dumps(jobs, indent=2, ensure_ascii=False)

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_content}
            ]
        )
        
        # Extração básica do JSON da resposta
        content = response.content[0].text
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            data = json.loads(json_str)
            return data.get("scored_jobs", [])
        else:
            print(f"[score.py] ✗ Não foi possível encontrar JSON na resposta do Claude.")
            return []

    except Exception as e:
        print(f"[score.py] ✗ Erro ao chamar Claude: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Pontua vagas via Claude Haiku")
    parser.add_argument("--date", default=str(date.today()), help="Data no formato YYYY-MM-DD")
    args = parser.parse_args()

    # Procura pelo arquivo raw mais recente daquela data
    raw_dir = Path("data/raw")
    raw_files = sorted(raw_dir.glob(f"{args.date}*.json"), reverse=True)
    
    if not raw_files:
        print(f"[score.py] ❌ Nenhum arquivo encontrado para a data: {args.date}")
        print("[score.py] Execute fetch.py primeiro.")
        return

    raw_path = raw_files[0]
    
    # Adicionando timestamp para evitar sobrescrita
    timestamp = datetime.now().strftime("%H%M%S")
    scored_filename = f"{args.date}_{timestamp}.json"
    scored_path = Path("data/scored") / scored_filename
    scored_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[score.py] Pontuando vagas de {raw_path.name}...")

    try:
        raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
        jobs = raw_data.get("jobs", [])
        
        if not jobs:
            print("[score.py] ⚠️ Nenhuma vaga encontrada no arquivo raw.")
            return

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("[score.py] ✗ Erro: ANTHROPIC_API_KEY não encontrada.")
            return

        client = Anthropic(api_key=api_key)
        profile = load_profile("config/profile.md")
        
        scored_jobs = score_jobs(client, jobs, profile)
        
        # Filtra apenas o topo ou as relevantes (estamos salvando todas mas marcando score)
        # O ROADMAP pede top vagas, score >= 80 no JSON final
        top_jobs = [j for j in scored_jobs if j.get("score", 0) >= 80]
        
        # Merge de informações extras do raw (empresa, source, etc) que o score pode ter omitido
        # mas para o MVP/POC, a estrutura do prompt já pede o básico.
        
        output_data = {
            "scored_at": date.today().isoformat(),
            "source_file": raw_path.name,
            "total_scored": len(scored_jobs),
            "total_top": len(top_jobs),
            "jobs": top_jobs
        }

        scored_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[score.py] ✅ Sucesso! {len(top_jobs)} vagas (score >= 80) salvas em {scored_path}")

    except Exception as e:
        print(f"[score.py] ✗ Ocorreu um erro: {e}")

if __name__ == "__main__":
    main()
