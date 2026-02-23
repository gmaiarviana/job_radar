"""
fetch.py — Busca vagas via OpenAI Responses API com web_search_preview.

Épico 1.3 | Salva em data/raw/YYYY-MM-DD.json

Uso:
    python src/fetch.py
    python src/fetch.py --date 2026-02-22
"""

import os
import json
import yaml
import argparse
from datetime import date, datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Carrega variáveis do arquivo .env
load_dotenv()

def load_config():
    config_path = Path("config/search.yaml")
    if not config_path.exists():
        raise FileNotFoundError("Configuração config/search.yaml não encontrada.")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_openai_search(client, roles, locations, lookback_hours):
    """
    Executa a busca de vagas via OpenAI gpt-4o-mini com capacidades de busca web.
    """
    roles_str = ", ".join(roles)
    locs_str = ", ".join(locations)
    
    # Prompt de busca refinado (v5) - Foco em Localização Literal e Confiança
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

    print(f"[fetch.py] 📡 Iniciando busca web para: {roles_str}...")
    
    try:
        # Revertendo para o modelo especializado em busca
        # Removendo response_format pois o modelo de preview pode não suportar
        response = client.chat.completions.create(
            model="gpt-4o-mini-search-preview",
            messages=[
                {"role": "system", "content": "Você é um especialista em busca de vagas remotas. Use sua capacidade de busca web para encontrar informações reais e atuais."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content
        # Limpeza de blocos de código Markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        data = json.loads(content)
        return data.get("jobs", [])
        
    except Exception as e:
        print(f"[fetch.py] ✗ Erro na chamada OpenAI: {e}")
        return []
        
def remove_duplicates(new_jobs, raw_dir):
    """
    Remove vagas que já foram salvas nos últimos 7 dias.
    Uma vaga é duplicata se (título + empresa) já existem.
    """
    recent_keys = set()
    today = date.today()
    
    # Busca arquivos dos últimos 7 dias
    for i in range(8):  # 0 a 7 dias atrás
        d = today.replace(day=today.day - i) if today.day > i else today # Simplificado para o exemplo, mas vamos usar algo mais robusto
        # Melhor: listar todos os arquivos em raw_dir e filtrar por data no nome
        pass

    # Implementação robusta: lista todos os arquivos e filtra os recentes
    try:
        files = list(raw_dir.glob("*.json"))
        for f in files:
            # O nome do arquivo começa com YYYY-MM-DD
            try:
                file_date_str = f.name.split('_')[0]
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
                days_diff = (today - file_date).days
                if 0 <= days_diff <= 7:
                    with open(f, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        for job in data.get("jobs", []):
                            key = (job.get("title", "").strip().lower(), 
                                   job.get("company", "").strip().lower())
                            recent_keys.add(key)
            except (ValueError, IndexError):
                continue
    except Exception as e:
        print(f"[fetch.py] ! Aviso ao ler duplicatas: {e}")

    filtered_jobs = []
    removed_recent = 0
    removed_batch = 0
    seen_in_batch = set()
    
    for job in new_jobs:
        # Case-insensitive key for comparison
        title = str(job.get("title", "") or "").strip().lower()
        company = str(job.get("company", "") or "").strip().lower()
        key = (title, company)
        
        if key in recent_keys:
            removed_recent += 1
            continue
            
        if key in seen_in_batch:
            removed_batch += 1
            continue
            
        # If not seen before, add to batch and filtered list
        filtered_jobs.append(job)
        seen_in_batch.add(key)
    
    # Logging as requested
    if removed_recent > 0:
        print(f"[fetch.py] 🧹 Removidas {removed_recent} vagas duplicatas já existentes (últimos 7 dias).")
    if removed_batch > 0:
        print(f"[fetch.py] 🧹 Removidas {removed_batch} duplicatas no mesmo lote.")
    
    return filtered_jobs

def filter_old_jobs(jobs):
    """
    Descarta vagas com mais de 14 dias com base no campo 'date'.
    Ex: '3 weeks ago', '1 month ago'.
    """
    filtered_jobs = []
    discarded_count = 0
    
    # Padrões que indicam mais de 14 dias
    old_patterns = ["week ago", "weeks ago", "month", "months"] # '1 week ago' pode ser 7 dias, mas '2 weeks' é 14. 
    # Sendo conservador: '3 weeks', 'month', 'months' definitivamente > 14 dias.
    # '2 weeks ago' pode ser exatamente 14 dias. O pedido diz "mais de 14 dias".
    
    critical_patterns = ["3 weeks", "4 weeks", "month", "months"]

    for job in jobs:
        date_str = job.get("date", "").lower()
        is_old = False
        
        # Lógica simples de busca de texto
        for p in critical_patterns:
            if p in date_str:
                is_old = True
                break
        
        # '2 weeks ago' -> depende se é mais de 14 dias. Geralmente 14 dias é o limite.
        if "2 weeks ago" in date_str:
            is_old = True # 14 dias ou mais
            
        if is_old:
            discarded_count += 1
        else:
            filtered_jobs.append(job)
            
    if discarded_count > 0:
        print(f"[fetch.py] ⏳ Descartadas {discarded_count} vagas antigas (> 14 dias).")
        
    return filtered_jobs

def main():
    parser = argparse.ArgumentParser(description="Busca vagas via OpenAI web search")
    parser.add_argument("--date", default=str(date.today()), help="Data no formato YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Apenas mostra o que seria buscado")
    args = parser.parse_args()

    # Setup paths
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%H%M%S")
    output_path = output_dir / f"{args.date}_{timestamp}.json"

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"[fetch.py] ✗ Erro ao carregar config: {e}")
        return

    search_config = config.get("search", {})
    roles = search_config.get("roles", ["Product Manager"])
    locations = search_config.get("locations", ["remote"])
    lookback_hours = search_config.get("lookback_hours", 24)

    # Run Fetch
    if args.dry_run:
        print("[fetch.py] 🧪 MODO DRY-RUN")
        print(f"  Configuração lida:")
        print(f"    Roles: {roles}")
        print(f"    Locations: {locations}")
        print(f"    Lookback: {lookback_hours}h")
        print(f"  A chamada para OpenAI usaria o modelo: gpt-4o-mini-search-preview")
        print(f"  O prompt gerado seria enviado agora.")
        jobs = []
    else:
        # Initialize OpenAI Client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[fetch.py] ✗ Erro: OPENAI_API_KEY não encontrada no ambiente.")
            return
        
        client = OpenAI(api_key=api_key)

        print(f"[fetch.py] 🚀 Buscando vagas para {args.date}...")
        jobs = run_openai_search(client, roles, locations, lookback_hours)

    # Filter and Deduplicate
    if jobs:
        jobs = filter_old_jobs(jobs)
        jobs = remove_duplicates(jobs, output_dir)

    # Save results
    output_data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "date": args.date,
        "config_used": {
            "roles": roles,
            "locations": locations,
            "lookback_hours": lookback_hours
        },
        "total_jobs": len(jobs),
        "jobs": jobs
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"[fetch.py] ✅ Sucesso! {len(jobs)} vagas salvas em {output_path}")

if __name__ == "__main__":
    main()
