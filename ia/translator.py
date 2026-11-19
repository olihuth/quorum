import json
import logging
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from metrics import compute_translation_metrics

logger = logging.getLogger(__name__)

GEMINI_ENDPOINT_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

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

SYSTEM_PROMPT_FALLBACK = (
    "Você é o tradutor cidadão do Quorum. Traduza a proposição abaixo do juridiquês "
    "para português brasileiro simples e neutro. Responda APENAS em JSON com as chaves: "
    '"bullets" (array com exatamente 3 frases curtas de 12 a 18 palavras), '
    '"detected_theme" (string curta), "citizen_impact_level" ("Alto", "Médio" ou "Baixo"), '
    'e "key_terms_explained" (array de até 3 objetos {"term": str, "plain_meaning": str}).'
)


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / "desjuridiques_v1.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return SYSTEM_PROMPT_FALLBACK


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
    system_prompt = _load_system_prompt()
    user_payload = (
        f"Traduza a seguinte proposição legislativa brasileira para Desjuridiquês.\n\n"
        f"Título: {title}\n"
        f"Texto Oficial: {official_summary}"
    )

    url = GEMINI_ENDPOINT_TEMPLATE.format(model=model)
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_payload}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    query = urllib.parse.urlencode({"key": api_key})
    request = urllib.request.Request(
        f"{url}?{query}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60.0) as response:
        if response.status >= 400:
            raise RuntimeError(f"Gemini API returned HTTP {response.status}")
        data = json.loads(response.read().decode("utf-8"))

    raw_text = _extract_gemini_json_text(data)
    parsed = json.loads(raw_text)
    bullets = [str(b).strip() for b in parsed.get("bullets", []) if str(b).strip()][:3]
    if len(bullets) < 3:
        raise ValueError("Gemini output returned fewer than 3 bullets.")

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


def translate_bill(
    title: str,
    official_summary: str,
    api_key: str | None = None,
    model: str | None = None,
) -> dict[str, object]:
    """Translate a Brazilian bill into plain-language Desjuridiquês with measured gains."""
    resolved_key = (
        api_key
        if api_key is not None
        else (os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or "")
    ).strip()
    resolved_model = (model or os.getenv("LLM_MODEL") or "gemini-4-hydrogen").strip()

    if resolved_key:
        try:
            result = _call_gemini(title, official_summary, resolved_key, resolved_model)
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
