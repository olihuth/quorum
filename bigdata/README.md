# Módulo Big Data & Analytics — Quorum

Este diretório concentra a arquitetura analítica de **Big Data e Visualização** (Área 2 — FIAP Global Solution 2026/2) da plataforma **Quorum**, estruturada no padrão **Medallion Architecture (Bronze → Silver → Gold)** e integrada tanto ao PostgreSQL 16 quanto ao painel **Panorama Legislativo** (`frontend/src/pages/DashboardPage.tsx`).

## Conteúdo do Módulo

| Arquivo / Pasta | Finalidade |
| --- | --- |
| [`DATA_ARCHITECTURE.md`](./DATA_ARCHITECTURE.md) | Documentação completa das camadas Bronze, Silver e Gold, diagramas Mermaid de fluxo e Entidade-Relacionamento, dicionário de dados e governança LGPD (SHA-256). |
| [`analytics_metrics.md`](./analytics_metrics.md) | Definições matemáticas, SQL (PostgreSQL 16) e fórmulas DAX (Power BI) das 4 métricas analíticas principais (`Citizen_Favor_Pct`, `Convergence_Index`, `Party_Fragmentation_HHI` e `Omnichannel_Participation_Rate`). |
| [`sql/medallion_gold_views.sql`](./sql/medallion_gold_views.sql) | Views SQL da camada Gold (`gold_party_seat_composition`, `gold_bill_convergence_metrics`, `gold_house_kpis`, `gold_bronze_ingestion_audit`) prontas para materialização no PostgreSQL 16. |
| [`pipeline_etl.py`](./pipeline_etl.py) | Pipeline ETL standalone (stdlib Python) que extrai dados da API FastAPI (`/api/v1`) com fallback offline resiliente, executa anonimização SHA-256 + deduplicação e gera artefatos em `./lakehouse/{bronze,silver,gold}`. |

## 1. Como Executar o Pipeline ETL (Bronze → Silver → Gold)

O script utiliza apenas biblioteca padrão do Python (sem dependências externas):

```powershell
cd bigdata
python pipeline_etl.py
```

- Se o backend FastAPI estiver ativo em `http://localhost:8000`, o pipeline consome os dados reais de `/api/v1/houses`, `/api/v1/bills` e `/api/v1/dashboard/overview`.
- Caso a API esteja offline, um snapshot legislativo realista é acionado automaticamente para garantir reprodutibilidade em avaliações e ambientes isolados.
- É possível apontar outra URL via variável de ambiente `QUORUM_API_BASE_URL`.

## 2. Como Materializar as Views Gold no PostgreSQL (Docker)

Com os containers do `docker-compose.yml` em execução (`quorum-postgres` saudável na porta `5432`):

```powershell
Get-Content .\sql\medallion_gold_views.sql | docker exec -i quorum-postgres psql -U quorum -d quorum_db
```

Para consultar os indicadores Gold diretamente no banco:

```sql
SELECT house_short_name, monitored_bills_count, avg_convergence_index, party_fragmentation_index
FROM gold_house_kpis
ORDER BY avg_convergence_index DESC;
```
