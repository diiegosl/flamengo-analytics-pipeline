# 🔴⚫ Flamengo Analytics: Pipeline de Dados & Dashboard (2024)

Projeto de análise de dados *End-to-End* do Clube de Regatas do Flamengo nas campanhas da Copa do Brasil e Série A (2024), combinando coleta via API, armazenamento relacional e modelagem visual no Power BI.

---

## 🛠️ Tecnologias e Ferramentas
- **Linguagem:** Python 3.x (Requisições HTTP, tratamento e limpeza de dados com biblioteca `requests`)
- **Banco de Dados:** PostgreSQL (Modelagem relacional e persistência de dados via `psycopg2`)
- **Visualização:** Power BI (Modelagem DAX e dashboard interativo)
- **Fonte de Dados:** API-Sports (API-Football)

---

## 📐 Arquitetura da Solução
1. **Extração:** Script em Python configurado com lógica de retentativas (*retry*) e pausas controladas para consumir a API respeitando os limites de requisição.
2. **Tratamento:** Limpeza e conversão dos dados brutos recebidos em formato JSON.
3. **Carga (EtL):** Inserção e atualização relacional (`ON CONFLICT DO UPDATE`) na tabela do PostgreSQL.
4. **Visualização:** Conexão do Power BI para análise de métricas de desempenho.

---

## 📈 Principais Insights do Painel

- **Desempenho Geral:** O Flamengo atingiu **72 gols marcados**, **28 vitórias** e uma taxa de eficiência (*Win Rate*) de **58%** nas competições analisadas (Copa do Brasil e Série A 2024).
- **Volume vs. Eficiência Ofensiva:** Acompanhamento temporal da relação entre o total de finalizações executadas, os chutes no alvo e a taxa de precisão das pontarias ao longo dos meses.
- **Rendimento Mandante x Visitante (*Home vs. Away*):** Comparativo do volume de vitórias e aproveitamento jogando no Maracanã versus atuações fora de casa.
- **Principais Vítimas (*Top 5 Victims*):** Destaque para os adversários que mais sofreram gols da equipe na temporada, liderados por Atlético-MG (8 gols) e Vasco da Gama (7 gols).
   
### 📊 Dashboard do Power BI

![Dashboard Power BI](power%20bi%20flamengo.jpg)
