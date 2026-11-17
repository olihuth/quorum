import re


def generate_desjuridiques(title: str, official_summary: str) -> list[str]:
    """Generate 3 plain-language Brazilian Portuguese bullet points for a bill.

    Currently implemented as a deterministic mocked translator so the backend
    runs predictably offline and in tests without requiring an external LLM key.
    """
    clean_title = re.sub(r"\s+", " ", (title or "Proposição legislativa")).strip().rstrip(".")
    clean_summary = re.sub(r"\s+", " ", (official_summary or "")).strip()

    topic_hint = "políticas públicas e regras administrativas"
    lowered = f"{clean_title} {clean_summary}".lower()
    if any(k in lowered for k in ("transporte", "mobilidade", "tarifa", "ônibus", "metrô")):
        topic_hint = "mobilidade urbana e transporte coletivo acessível"
    elif any(k in lowered for k in ("transparência", "dados abertos", "compras", "licitação", "auditoria")):
        topic_hint = "transparência pública e controle dos gastos governamentais"
    elif any(k in lowered for k in ("solar", "energia", "fotovoltaica", "elétrica")):
        topic_hint = "incentivo à energia limpa e redução na conta de luz"
    elif any(k in lowered for k in ("água", "hídrica", "drenagem", "enchente", "chuva")):
        topic_hint = "segurança hídrica, drenagem urbana e prevenção de alagamentos"
    elif any(k in lowered for k in ("escola", "educação", "estudante", "internet")):
        topic_hint = "conectividade escolar e proteção de dados de estudantes"

    summary_excerpt = clean_summary[:180].rstrip(" .") if clean_summary else clean_title
    if len(clean_summary) > 180:
        summary_excerpt += "..."

    return [
        f"Objetivo direto: a proposta trata de {topic_hint}, tendo como foco principal \"{clean_title}\".",
        f"O que muda na prática: {summary_excerpt}.",
        "Impacto para o cidadão: amplia a previsibilidade, a transparência e o acompanhamento social antes da votação oficial.",
    ]
