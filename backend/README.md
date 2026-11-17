# Quorum Backend — FastAPI, Arquitetura Medalhão & PostgreSQL 16

API REST do **Quorum** construída com Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, httpx e APScheduler, seguindo a **Arquitetura Medalhão (Bronze → Silver → Gold)**.

## Arquitetura de Dados (Medalhão)

- **Bronze (`raw_legislative_events`):** Armazenamento bruto (`JSONB`) das respostas das APIs oficiais da Câmara dos Deputados e do Senado Federal.
- **Silver (`legislative_houses`, `parties`, `politicians`, `bills`, `official_votes`, `citizen_votes`, `users`):** Entidades relacionais normalizadas com unicidade de voto cidadão por `UniqueConstraint(bill_id, citizen_hash)` via hash SHA-256 (LGPD).
- **Gold (`GET /api/v1/houses/*`, `GET /api/v1/dashboard/overview`):** Agregações analíticas prontas para consumo pelo painel *Panorama Legislativo* (composição percentual de bancadas e comparativo Enquete Cidadã web + IoT vs. aprovação oficial).

## Como Executar com Docker Compose (Recomendado com PostgreSQL 16)

Na raiz do monorepo (`GS2/`):

```bash
docker compose up --build
```

- API FastAPI: `http://localhost:8000`
- Documentação Swagger: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`

## Como Executar Localmente sem Docker (SQLite automático)

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Executar Testes Automatizados (`pytest`)

```bash
cd backend
pytest -v
```

## Principais Endpoints (`/api/v1`)

| Método | Rota | Descrição |
| --- | --- | --- |
| `GET` | `/health` | Verificação de disponibilidade da API |
| `GET` | `/api/v1/houses` | Lista as 5 Casas Legislativas com composição de bancadas |
| `GET` | `/api/v1/houses/{slug}` | Detalhe e agenda da Casa Legislativa |
| `GET` | `/api/v1/politicians` | Perfis somente leitura filtráveis (`house_slug`, `party_acronym`, `search`) |
| `GET` | `/api/v1/politicians/{id}` | Histórico oficial de votações e projetos de autoria |
| `GET` | `/api/v1/bills` | Projetos de Lei com resumo *Desjuridiquês* e parciais de voto |
| `POST` | `/api/v1/bills/{id}/vote` | Registra 1 voto anonimizado (SHA-256) por cidadão (`409` se duplicado) |
| `POST` | `/api/v1/bills/{id}/like` | Incrementa contador de apoio à pauta |
| `POST` | `/api/v1/iot/vote` | Ingestão de votos vindos de totens físicos Arduino/Tinkercad (`source=iot_totem`) |
| `GET` | `/api/v1/dashboard/overview` | Métricas Gold Layer para o *Panorama Legislativo* |
| `POST` | `/api/v1/auth/register` | Cadastro de conta cidadã privada (e-mail + senha) |
| `POST` | `/api/v1/auth/login` | Autenticação com retorno de token Bearer |
| `GET` / `PATCH` | `/api/v1/users/me` | Consulta e atualização de configurações privadas do usuário |
| `POST` | `/api/v1/admin/sync/politicians` | Dispara sincronização manual da Trilha A (requer header `X-Admin-Key`) |
| `POST` | `/api/v1/admin/sync/bills` | Dispara varredura manual da Trilha B (requer header `X-Admin-Key`) |
