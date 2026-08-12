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
   
### 📊 Dashboard do Power BI

![Dashboard Power BI](power%20bi%20flamengo.jpg)
