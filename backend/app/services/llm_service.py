import json
import logging
import re

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

GEMINI_ENDPOINT_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

VOWEL_CLUSTER_RE = re.compile(r"[aeiouáéíóúâêîôûãõàü]+", re.IGNORECASE)
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+")
SENTENCE_SPLIT_RE = re.compile(r"[.!?;\n]+")

JARGON_GLOSSARY: list[tuple[str, str, str]] = [
    (
        "não cumulatividade plena",
        "Não cumulatividade plena",
        "Imposto pago em uma etapa vira crédito integral para não cobrar imposto sobre imposto.",
    ),
    (
        "alíquota de referência",
        "Alíquota de referência",
        "Percentual padrão calculado para manter a arrecadação atual sem aumentar a carga total.",
    ),
    (
        "impacto algorítmico",
        "Avaliação de impacto algorítmico",
        "Análise prévia para checar se um sistema de IA discrimina ou prejudica cidadãos.",
    ),
    (
        "responsabilidade civil objetiva",
        "Responsabilidade civil objetiva",
        "A empresa responde pelos danos causados mesmo sem precisar provar intenção ou culpa.",
    ),
    (
        "perfilamento",
        "Perfilamento comercial",
        "Criação de perfis de comportamento usados para direcionar anúncios ou ofertas.",
    ),
    (
        "caixas de recompensa",
        "Caixas de recompensa (loot boxes)",
        "Pacotes pagos dentro de jogos eletrônicos com itens aleatórios parecidos com apostas.",
    ),
    (
        "intermodal",
        "Integração intermodal",
        "Conexão fácil entre ônibus, metrô, trem e bicicleta no mesmo trajeto.",
    ),
    (
        "subvenção econômica",
        "Subvenção econômica",
        "Dinheiro público usado para baratear um serviço ou projeto de interesse social.",
    ),
    (
        "georreferenciado",
        "Dados georreferenciados",
        "Informações ligadas ao endereço ou mapa exato de onde a obra acontece.",
    ),
    (
        "dispensa de licitação",
        "Dispensa de licitação",
        "Compra feita pelo governo sem concorrência comum em casos previstos em lei.",
    ),
    (
        "aditivos",
        "Aditivos financeiros",
        "Alterações posteriores que aumentam o valor ou o prazo de um contrato público.",
    ),
    (
        "hidrometeorológico",
        "Monitoramento hidrometeorológico",
        "Acompanhamento em tempo real do volume de chuvas e do nível dos rios.",
    ),
    (
        "microgeração",
        "Microgeração distribuída",
        "Produção própria de energia elétrica limpa em pequena escala, como placas solares.",
    ),
    (
        "dotação orçamentária",
        "Dotação orçamentária",
        "Reserva de dinheiro já prevista no orçamento público para pagar a ação.",
    ),
]

SYSTEM_PROMPT = (
    "Você é o tradutor cidadão da plataforma Quorum no Brasil. "
    "Traduza a proposição legislativa abaixo do juridiquês para português brasileiro simples do dia a dia, "
    "usando palavras curtas e comuns que qualquer pessoa entende na hora. "
    "PROIBIDO repetir palavras longas ou termos jurídicos dentro de 'bullets' (substitua palavras como "
    "'governança', 'discriminatórios', 'responsabilidade', 'cumulatividade', 'perfilamento' por termos "
    "simples como 'regras', 'preconceito', 'pagar por danos', 'imposto duplo', 'espionar dados'); "
    "mantenha os termos técnicos apenas em 'key_terms_explained'. "
    "Responda EXCLUSIVAMENTE em JSON válido com as chaves:\n"
    '- "bullets": array com exatamente 3 frases curtas de 10 a 16 palavras cada\n'
    '- "detected_theme": string curta com o tema principal\n'
    '- "citizen_impact_level": "Alto", "Médio" ou "Baixo"\n'
    '- "key_terms_explained": array de até 3 objetos {"term": string, "plain_meaning": string simples}'
)


def _count_portuguese_syllables(word: str) -> int:
    clusters = VOWEL_CLUSTER_RE.findall(word)
    return max(1, len(clusters))


def calculate_portuguese_readability(text: str) -> float:
    """Compute Flesch Reading Ease adapted for Brazilian Portuguese (Martins et al.)."""
    words = WORD_RE.findall(text or "")
    if not words:
        return 0.0
    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(text or "") if s.strip()]
    sentence_count = max(1, len(sentences))
    word_count = len(words)
    syllable_count = sum(_count_portuguese_syllables(w) for w in words)

    score = (
        248.835
        - 1.015 * (word_count / sentence_count)
        - 84.6 * (syllable_count / word_count)
    )
    return round(max(0.0, min(100.0, score)), 1)


def _classify_readability(score: float) -> str:
    if score >= 75.0:
        return "Muito Fácil"
    if score >= 50.0:
        return "Fácil"
    if score >= 25.0:
        return "Médio"
    return "Muito Difícil (Juridiquês)"


def _estimate_reading_time_sec(word_count: int, words_per_minute: int) -> int:
    if word_count <= 0:
        return 0
    return max(1, round((word_count / words_per_minute) * 60))


def compute_translation_metrics(original_text: str, bullets: list[str]) -> dict[str, object]:
    """Calculate before-vs-after readability, word reduction, and time saved."""
    summary_text = " ".join(b.rstrip(" .") + "." for b in bullets if b.strip())
    original_words = len(WORD_RE.findall(original_text or ""))
    summary_words = len(WORD_RE.findall(summary_text))

    flesch_before = calculate_portuguese_readability(original_text)
    flesch_after = calculate_portuguese_readability(summary_text)

    time_before_sec = _estimate_reading_time_sec(original_words, words_per_minute=120)
    time_after_sec = _estimate_reading_time_sec(summary_words, words_per_minute=180)
    time_saved_sec = max(0, time_before_sec - time_after_sec)

    reduction_pct = (
        round(((original_words - summary_words) / original_words) * 100, 1)
        if original_words > 0
        else 0.0
    )

    return {
        "original_word_count": original_words,
        "summary_word_count": summary_words,
        "word_reduction_pct": max(0.0, reduction_pct),
        "flesch_before": flesch_before,
        "flesch_after": flesch_after,
        "readability_gain_points": round(flesch_after - flesch_before, 1),
        "level_before": _classify_readability(flesch_before),
        "level_after": _classify_readability(flesch_after),
        "reading_time_before_sec": time_before_sec,
        "reading_time_after_sec": time_after_sec,
        "reading_time_saved_sec": time_saved_sec,
    }


def _detect_topic(text: str) -> tuple[str, str, str]:
    lowered = text.lower()
    if any(k in lowered for k in ("inteligência artificial", "algorítmico", "alto risco", "automatizadas")):
        return (
            "Regulação de Inteligência Artificial",
            "Alto",
            "Garante transparência, revisão humana e direito à explicação quando uma IA decide sobre sua vida.",
        )
    if any(k in lowered for k in ("tributária", "ibs", "cbs", "alíquota", "cashback", "cesta básica")):
        return (
            "Reforma Tributária e Impostos",
            "Alto",
            "Simplifica impostos sobre consumo, zera a alíquota da cesta básica e cria devolução de imposto para baixa renda.",
        )
    if any(k in lowered for k in ("criança", "adolescente", "etária", "perfilamento", "loot boxes", "recompensa")):
        return (
            "Proteção Digital de Crianças",
            "Alto",
            "Impede propaganda direcionada a menores em redes sociais e reforça a verificação de idade.",
        )
    if any(k in lowered for k in ("transporte", "mobilidade", "tarifa", "ônibus", "metrô")):
        return (
            "Mobilidade Urbana",
            "Alto",
            "Melhora o deslocamento diário e o acesso ao transporte público na cidade.",
        )
    if any(k in lowered for k in ("transparência", "dados abertos", "compras", "licitação", "auditoria", "aditivo")):
        return (
            "Transparência e Contratos Públicos",
            "Alto",
            "Facilita a fiscalização cidadã dos gastos públicos e ajuda a evitar desperdícios.",
        )
    if any(k in lowered for k in ("solar", "energia", "fotovoltaica", "elétrica", "microgeração")):
        return (
            "Energia Limpa",
            "Alto",
            "Amplia o acesso à energia solar e pode reduzir o valor da conta de luz.",
        )
    if any(k in lowered for k in ("água", "hídrica", "drenagem", "enchente", "chuva", "saneamento")):
        return (
            "Segurança Hídrica e Clima",
            "Alto",
            "Protege bairros vulneráveis contra enchentes e garante segurança no abastecimento.",
        )
    if any(k in lowered for k in ("escola", "educação", "estudante", "internet", "conectividade")):
        return (
            "Educação e Inclusão Digital",
            "Alto",
            "Melhora a qualidade do ensino público e protege os dados pessoais de crianças e jovens.",
        )
    return (
        "Administração Pública",
        "Médio",
        "Traz mais clareza e regras definidas para o funcionamento do serviço público.",
    )


def _extract_jargon(text: str) -> list[dict[str, str]]:
    lowered = text.lower()
    matches: list[dict[str, str]] = []
    for needle, label, meaning in JARGON_GLOSSARY:
        if needle in lowered:
            matches.append({"term": label, "plain_meaning": meaning})
        if len(matches) >= 3:
            break
    if not matches:
        matches.append(
            {
                "term": "Ementa legislativa",
                "plain_meaning": "Resumo oficial que apresenta o objetivo jurídico de um projeto de lei.",
            }
        )
    return matches


def _fallback_translate(title: str, official_summary: str) -> dict[str, object]:
    clean_title = re.sub(r"\s+", " ", (title or "Proposição legislativa")).strip().rstrip(".")
    clean_summary = re.sub(r"\s+", " ", (official_summary or "")).strip()
    combined = f"{clean_title} {clean_summary}"
    theme, impact_level, citizen_effect = _detect_topic(combined)

    clean_body = re.sub(
        r"^(?:Art\.?|Artigo|§)\s*\d+[º°]?\s*[-–]?\s*",
        "",
        clean_summary,
        flags=re.IGNORECASE,
    ).strip()
    first_clause = re.split(r"[.;]", clean_body)[0].strip() if clean_body else clean_title
    if len(first_clause) > 88:
        first_clause = first_clause[:88].rsplit(" ", 1)[0].rstrip(",;. ") + "..."
    else:
        first_clause = first_clause.rstrip(",;. ")

    second_body = first_clause[0].lower() + first_clause[1:] if len(first_clause) > 1 else first_clause
    second_bullet = f"Na prática, {second_body}"
    if not second_bullet.endswith("."):
        second_bullet += "."

    bullets = [
        f"Trata de {theme.lower()} por meio da proposta \"{clean_title}\".",
        second_bullet,
        citizen_effect,
    ]
    return {
        "bullets": bullets,
        "detected_theme": theme,
        "citizen_impact_level": impact_level,
        "key_terms_explained": _extract_jargon(combined),
        "provider": "fallback_deterministic",
        "model": "quorum-rule-engine-v1",
    }


def _extract_gemini_json_text(data: dict) -> str:
    """Extract final JSON text while skipping Gemini 4 Hydrogen thinking parts."""
    parts = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [])
    )
    raw_text = ""
    for part in parts:
        if isinstance(part, dict) and not part.get("thought", False) and part.get("text"):
            raw_text = str(part["text"]).strip()
            break
    if not raw_text and parts and isinstance(parts[-1], dict):
        raw_text = str(parts[-1].get("text", "")).strip()

    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.DOTALL).strip()
    return raw_text


def _call_gemini(
    title: str,
    official_summary: str,
    api_key: str,
    model: str,
) -> dict[str, object]:
    user_payload = (
        f"Traduza a seguinte proposição legislativa brasileira para Desjuridiquês.\n\n"
        f"Título: {title}\n"
        f"Texto Oficial: {official_summary}"
    )

    url = GEMINI_ENDPOINT_TEMPLATE.format(model=model)
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_payload}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, params={"key": api_key}, json=body)
        response.raise_for_status()
        data = response.json()

    raw_text = _extract_gemini_json_text(data)
    parsed = json.loads(raw_text)
    bullets = [str(b).strip() for b in parsed.get("bullets", []) if str(b).strip()][:3]
    if len(bullets) < 3:
        raise ValueError("Gemini returned fewer than 3 bullets.")

    terms = []
    for item in parsed.get("key_terms_explained", [])[:3]:
        if isinstance(item, dict) and item.get("term") and item.get("plain_meaning"):
            terms.append(
                {
                    "term": str(item["term"]).strip(),
                    "plain_meaning": str(item["plain_meaning"]).strip(),
                }
            )

    impact = str(parsed.get("citizen_impact_level", "Médio")).strip()
    if impact not in ("Alto", "Médio", "Baixo"):
        impact = "Médio"

    return {
        "bullets": bullets,
        "detected_theme": str(parsed.get("detected_theme", "Legislação Cidadã")).strip(),
        "citizen_impact_level": impact,
        "key_terms_explained": terms or _extract_jargon(f"{title} {official_summary}"),
        "provider": "google_gemini",
        "model": model,
    }


def translate_bill_preview(title: str, official_summary: str) -> dict[str, object]:
    """Translate a bill using Gemini 4 Hydrogen (with fallback) and measure gains."""
    settings = get_settings()
    api_key = settings.resolved_llm_api_key
    model = settings.llm_model or "gemini-4-hydrogen"

    if api_key:
        try:
            result = _call_gemini(title, official_summary, api_key, model)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Gemini API call failed (%s); falling back to deterministic engine.",
                exc,
            )
            result = _fallback_translate(title, official_summary)
    else:
        result = _fallback_translate(title, official_summary)

    original_full = f"{title}. {official_summary}".strip()
    metrics = compute_translation_metrics(original_full, result["bullets"])
    return {
        **result,
        "metrics": metrics,
    }


def generate_desjuridiques(title: str, official_summary: str) -> list[str]:
    """Return 3 plain-language Brazilian Portuguese bullet points for ingestion workers."""
    return translate_bill_preview(title, official_summary)["bullets"]
