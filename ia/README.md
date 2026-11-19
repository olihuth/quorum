# Quorum IA — Módulo "Desjuridiquês" (Google Gemini 4 Hydrogen)

Módulo responsável pela tradução automática de Projetos de Lei (PLs) do jargão jurídico para linguagem cidadã em português brasileiro (pt-BR), acompanhado de métricas objetivas de ganho de legibilidade.

## Arquitetura do Módulo

- [prompts/desjuridiques_v1.md](prompts/desjuridiques_v1.md): Prompt de sistema versionado com regras de neutralidade cívica, esquema JSON estrito e exemplo *few-shot*.
- [translator.py](translator.py): Integração via REST com **Google Gemini 4 Hydrogen (`gemini-4-hydrogen`)** em modo JSON estruturado (`responseMimeType: application/json`), ignorando partes de raciocínio (`thought: true`), com *fallback* determinístico automático caso nenhuma chave de API esteja configurada.
- [metrics.py](metrics.py): Cálculo do índice **Flesch Reading Ease adaptado ao Português (Martins et al.)**, redução percentual de palavras e tempo estimado de leitura economizado.
- [evaluate_metrics.py](evaluate_metrics.py): Script de avaliação em lote com textos legislativos reais e densos, demonstração de entrada/saída e comparativo antes vs. depois.

## Como Executar a Avaliação e Demonstração

### Modo offline (fallback determinístico, sem chave)
```bash
cd ia
pip install -r requirements.txt
python evaluate_metrics.py
```

### Modo com LLM real (Google Gemini 4 Hydrogen)
1. Gere uma chave gratuita em https://aistudio.google.com/apikey
2. Defina a variável de ambiente localmente (sem versionar no Git):
   ```powershell
   $env:LLM_API_KEY="SUA_CHAVE_GEMINI_AQUI"
   python evaluate_metrics.py
   ```
