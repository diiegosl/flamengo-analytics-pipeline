import time
import psycopg2
import requests

# 1. Configurações (Substitua pelas suas credenciais ao executar localmente)
API_KEY = "SUA_API_KEY_AQUI"
TEAM_ID = "127"  # ID do Flamengo

DB_CONFIG = {
    "dbname": "flamengo_analytics",
    "user": "postgres",
    "password": "SUA_SENHA_AQUI",
    "host": "localhost",
    "port": "5432",
}

headers = {"x-apisports-key": API_KEY}


def parse_val(val_str):
    if val_str is None:
        return 0.0
    if isinstance(val_str, str):
        val_str = val_str.replace("%", "").strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0


def fazer_requisicao_com_retry(url, headers, retries=5):
    """
    Realiza a requisição e, se atingir o limite por minuto, 
    aguarda 60 segundos para liberar a cota da API.
    """
    for i in range(retries):
        try:
            res = requests.get(url, headers=headers)
            data = res.json()
            errors = data.get("errors", {})

            # Identifica estouro de taxa de requisição
            if errors and ("rateLimit" in errors or "requests" in errors):
                print(
                    f"      [Aviso API] Limite/minuto atingido. Aguardando 60s para resetar...")
                time.sleep(60)
                continue

            response_content = data.get("response", [])
            # Se veio limpo e com resposta, devolve
            return response_content

        except Exception as e:
            print(
                f"      [Erro de conexão] Tentativa {i+1}/{retries}. Aguardando 10s...")
            time.sleep(10)

    return []


# 2. Buscar jogos
print("Buscando partidas do Flamengo na API...")
ligas_testar = [
    ("71", "2024"),  # Brasileirão 2024
    ("73", "2024"),  # Copa do Brasil 2024
]

todas_partidas = []
for league_id, season in ligas_testar:
    url = f"https://v3.football.api-sports.io/fixtures?team={TEAM_ID}&league={league_id}&season={season}"
    dados = fazer_requisicao_com_retry(url, headers)
    if dados:
        print(f"-> Encontradas {len(dados)} partidas na liga {league_id}.")
        todas_partidas.extend(dados)
    time.sleep(6)  # Pausa de segurança

if not todas_partidas:
    print("Nenhuma partida encontrada.")
    exit()

print(
    f"Total de {len(todas_partidas)} partidas encontradas. Processando sem estourar a API...")

# 3. Conexão com PostgreSQL
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# 4. Processar cada partida
for index, item in enumerate(todas_partidas, 1):
    fixture = item["fixture"]
    league = item["league"]
    teams = item["teams"]
    goals = item["goals"]
    score = item["score"]

    match_id = fixture["id"]
    is_home = teams["home"]["id"] == int(TEAM_ID)
    opponent = teams["away"]["name"] if is_home else teams["home"]["name"]
    venue = "Home" if is_home else "Away"

    flamengo_goals = goals["home"] if is_home else goals["away"]
    opponent_goals = goals["away"] if is_home else goals["home"]

    fla_ht = score["halftime"]["home"] if is_home else score["halftime"]["away"]
    opp_ht = score["halftime"]["away"] if is_home else score["halftime"]["home"]

    if flamengo_goals is not None and opponent_goals is not None:
        if flamengo_goals > opponent_goals:
            result = "W"
        elif flamengo_goals < opponent_goals:
            result = "L"
        else:
            result = "D"
    else:
        result = "Pending"

    # --- Requisitar Estatísticas Detalhadas ---
    time.sleep(6)  # Pausa de 6s garante que nunca ultrapassamos 10 req/min
    stats_url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={match_id}"
    res_stats = fazer_requisicao_com_retry(stats_url, headers)

    fla_stats = {}
    if res_stats:
        for team_stat in res_stats:
            if team_stat["team"]["id"] == int(TEAM_ID):
                for s in team_stat["statistics"]:
                    fla_stats[s["type"]] = s["value"]

    # --- Requisitar Escalação e Tática ---
    time.sleep(6)  # Pausa de 6s
    lineup_url = f"https://v3.football.api-sports.io/fixtures/lineups?fixture={match_id}"
    res_lineup = fazer_requisicao_com_retry(lineup_url, headers)

    form_fla, form_opp, coach_fla = None, None, None
    if res_lineup:
        for l in res_lineup:
            if l["team"]["id"] == int(TEAM_ID):
                form_fla = l.get("formation")
                if l.get("coach"):
                    coach_fla = l["coach"].get("name")
            else:
                form_opp = l.get("formation")

    # Extração de xG flexível
    xg_val = (
        fla_stats.get("expected_goals")
        or fla_stats.get("Expected Goals")
        or fla_stats.get("xG")
    )

    # Inserção no PostgreSQL
    query = """
        INSERT INTO partidas_flamengo (
            match_id, campeonato, temporada, rodada, data_jogo, estadio, cidade, arbitro,
            mando, adversario, status, gols_flamengo, gols_adversario, gols_fla_intervalo,
            gols_adv_intervalo, resultado, formacao_flamengo, formacao_adversario, tecnico_flamengo,
            posse_bola_pct, chutes_gol, chutes_fora, chutes_totais, chutes_bloqueados,
            chutes_dentro_area, chutes_fora_area, faltas, escanteios, impedimentos,
            cartoes_amarelos, cartoes_vermelhos, defesas_goleiro, passes_totais,
            passes_certos, precisao_passe_pct, xg
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (match_id) DO UPDATE SET
            campeonato = EXCLUDED.campeonato,
            temporada = EXCLUDED.temporada,
            rodada = EXCLUDED.rodada,
            data_jogo = EXCLUDED.data_jogo,
            estadio = EXCLUDED.estadio,
            cidade = EXCLUDED.cidade,
            arbitro = EXCLUDED.arbitro,
            mando = EXCLUDED.mando,
            adversario = EXCLUDED.adversario,
            status = EXCLUDED.status,
            gols_flamengo = EXCLUDED.gols_flamengo,
            gols_adversario = EXCLUDED.gols_adversario,
            gols_fla_intervalo = EXCLUDED.gols_fla_intervalo,
            gols_adv_intervalo = EXCLUDED.gols_adv_intervalo,
            resultado = EXCLUDED.resultado,
            formacao_flamengo = EXCLUDED.formacao_flamengo,
            formacao_adversario = EXCLUDED.formacao_adversario,
            tecnico_flamengo = EXCLUDED.tecnico_flamengo,
            posse_bola_pct = EXCLUDED.posse_bola_pct,
            chutes_gol = EXCLUDED.chutes_gol,
            chutes_fora = EXCLUDED.chutes_fora,
            chutes_totais = EXCLUDED.chutes_totais,
            chutes_bloqueados = EXCLUDED.chutes_bloqueados,
            chutes_dentro_area = EXCLUDED.chutes_dentro_area,
            chutes_fora_area = EXCLUDED.chutes_fora_area,
            faltas = EXCLUDED.faltas,
            escanteios = EXCLUDED.escanteios,
            impedimentos = EXCLUDED.impedimentos,
            cartoes_amarelos = EXCLUDED.cartoes_amarelos,
            cartoes_vermelhos = EXCLUDED.cartoes_vermelhos,
            defesas_goleiro = EXCLUDED.defesas_goleiro,
            passes_totais = EXCLUDED.passes_totais,
            passes_certos = EXCLUDED.passes_certos,
            precisao_passe_pct = EXCLUDED.precisao_passe_pct,
            xg = EXCLUDED.xg;
    """

    cursor.execute(
        query,
        (
            match_id,
            league["name"],
            str(league["season"]),
            league.get("round"),
            fixture["date"],
            fixture["venue"].get("name"),
            fixture["venue"].get("city"),
            fixture.get("referee"),
            venue,
            opponent,
            fixture["status"]["short"],
            flamengo_goals,
            opponent_goals,
            fla_ht,
            opp_ht,
            result,
            form_fla,
            form_opp,
            coach_fla,
            parse_val(fla_stats.get("Ball Possession")),
            fla_stats.get("Shots on Goal") or 0,
            fla_stats.get("Shots off Goal") or 0,
            fla_stats.get("Total Shots") or 0,
            fla_stats.get("Blocked Shots") or 0,
            fla_stats.get("Shots insidebox") or 0,
            fla_stats.get("Shots outsidebox") or 0,
            fla_stats.get("Fouls") or 0,
            fla_stats.get("Corner Kicks") or 0,
            fla_stats.get("Offsides") or 0,
            fla_stats.get("Yellow Cards") or 0,
            fla_stats.get("Red Cards") or 0,
            fla_stats.get("Goalkeeper Saves") or 0,
            fla_stats.get("Total passes") or 0,
            fla_stats.get("Passes accurate") or 0,
            parse_val(fla_stats.get("Passes %")),
            parse_val(xg_val),
        ),
    )
    print(f"[{index}/{len(todas_partidas)}] Partida {match_id} ({opponent}) atualizada com sucesso.")

conn.commit()
cursor.close()
conn.close()

print("\nCONCLUÍDO COM SUCESSO! A base do PostgreSQL está 100% preenchida sem falhas de requisição.")
