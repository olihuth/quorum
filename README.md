# Quorum — Transparência Legislativa e Participação Cidadã

Plataforma CitizenTech focada em transparência legislativa no Brasil, acompanhando Projetos de Lei (PLs) e votações oficiais no Congresso Nacional, Senado Federal, Assembleias Estaduais e Câmaras Municipais.

## Estrutura do Monorepo

- `/frontend` — Aplicação web em React + TypeScript + Vite + Tailwind CSS
- `/backend` — Serviços de API e persistência (módulo reservado)
- `/ia` — Pipeline de tradução jurídica (*Desjuridiquês*) e sumarização por IA (módulo reservado)
- `/bigdata` — Ingestão, camadas de dados e indicadores legislativos (módulo reservado)
- `/iot` — Integração de sensores e telemetria urbana/hídrica (módulo reservado)

## Como executar o Frontend

### Pré-requisitos
- Node.js 18+ (testado com Node.js v22 LTS)
- npm

### Instalação e execução local

```bash
cd frontend
npm install
npm run dev
```

### Build de produção

```bash
cd frontend
npm run build
```
