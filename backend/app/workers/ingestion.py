from collections import Counter
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.legislative import (
    Bill,
    LegislativeHouse,
    Party,
    Politician,
    RawLegislativeEvent,
)
from app.services.llm_service import generate_desjuridiques

logger = logging.getLogger(__name__)

CAMARA_DEPUTIES_URL = (
    "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome&itens=600"
)
SENADO_SENATORS_URL = "https://legis.senado.leg.br/dadosabertos/senador/lista/atual"
CAMARA_BILLS_URL = (
    "https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PL&itens=15&ordem=DESC&ordenarPor=id"
)

PARTY_COLORS: dict[str, str] = {
    "PL": "#1D4ED8",
    "PT": "#DC2626",
    "UNIÃO": "#0284C7",
    "PP": "#2563EB",
    "MDB": "#009C3B",
    "PSD": "#EAB308",
    "REPUBLICANOS": "#0EA5E9",
    "PSB": "#EA580C",
    "PSOL": "#9333EA",
    "PDT": "#D97706",
    "PODEMOS": "#10B981",
    "PODE": "#10B981",
    "AVANTE": "#F59E0B",
    "SOLIDARIEDADE": "#FB923C",
    "NOVO": "#F97316",
    "PCDOB": "#B91C1C",
    "PCdoB": "#B91C1C",
    "PV": "#16A34A",
    "CIDADANIA": "#EC4899",
    "PRD": "#4F46E5",
    "REDE": "#0D9488",
}

PARTY_NAMES: dict[str, str] = {
    "PL": "Partido Liberal",
    "PT": "Partido dos Trabalhadores",
    "UNIÃO": "União Brasil",
    "PP": "Progressistas",
    "MDB": "Movimento Democrático Brasileiro",
    "PSD": "Partido Social Democrático",
    "REPUBLICANOS": "Republicanos",
    "PSB": "Partido Socialista Brasileiro",
    "PSOL": "Partido Socialismo e Liberdade",
    "PDT": "Partido Democrático Trabalhista",
    "PODEMOS": "Podemos",
    "PODE": "Podemos",
    "AVANTE": "Avante",
    "SOLIDARIEDADE": "Solidariedade",
    "NOVO": "Partido Novo",
    "PCDOB": "Partido Comunista do Brasil",
    "PV": "Partido Verde",
    "CIDADANIA": "Cidadania",
    "PRD": "Partido Renovação Democrática",
    "REDE": "Rede Sustentabilidade",
}


def _party_color(acronym: str) -> str:
    return PARTY_COLORS.get(acronym) or PARTY_COLORS.get(acronym.upper()) or "#64748B"


def _party_full_name(acronym: str) -> str:
    return PARTY_NAMES.get(acronym) or PARTY_NAMES.get(acronym.upper()) or acronym


def _get_or_create_party(db: Session, acronym: str) -> Party:
    normalized = (acronym or "S.PART.").strip().upper()
    party = db.scalar(select(Party).where(Party.acronym == normalized))
    if party:
        if party.color_hex == "#64748B" and normalized in PARTY_COLORS:
            party.color_hex = PARTY_COLORS[normalized]
        return party
    party = Party(
        acronym=normalized,
        name=_party_full_name(normalized),
        color_hex=_party_color(normalized),
        spectrum="Diversos",
        program_summary="Bancada parlamentar com atuação sincronizada via API oficial do Legislativo.",
        official_portal_url="https://www.tse.jus.br/partidos/partidos-registrados-no-tse",
    )
    db.add(party)
    db.flush()
    return party


def _build_composition_json(seat_counts: Counter[str], db: Session) -> list[dict[str, object]]:
    """Convert raw party seat counts into sorted composition entries (top 9 + Outros)."""
    sorted_items = seat_counts.most_common()
    top_items = sorted_items[:9]
    remaining_seats = sum(count for _, count in sorted_items[9:])

    composition: list[dict[str, object]] = []
    for acronym, count in top_items:
        party = _get_or_create_party(db, acronym)
        composition.append(
            {
                "party": acronym,
                "party_name": party.name,
                "seat_count": count,
                "color_hex": _party_color(acronym),
            }
        )

    if remaining_seats > 0:
        composition.append(
            {
                "party": "Outros",
                "party_name": "Demais Partidos e Blocos",
                "seat_count": remaining_seats,
                "color_hex": "#64748B",
            }
        )

    return composition


def sync_politicians(db: Session) -> dict[str, object]:
    """Track A (Async Batch Sync): Fetch real deputies and senators into Bronze + Silver."""
    bronze_count = 0
    upserted_count = 0
    source_notes: list[str] = []

    camara_house = db.scalar(
        select(LegislativeHouse).where(LegislativeHouse.slug == "congresso-nacional")
    )
    senado_house = db.scalar(
        select(LegislativeHouse).where(LegislativeHouse.slug == "senado-federal")
    )

    with httpx.Client(timeout=20.0) as client:
        # 1. Câmara dos Deputados Open Data API (all active deputies)
        if camara_house:
            try:
                response = client.get(CAMARA_DEPUTIES_URL, headers={"Accept": "application/json"})
                response.raise_for_status()
                payload = response.json()
                deputies = payload.get("dados", [])
                camara_party_counts: Counter[str] = Counter()

                for dep in deputies:
                    ext_id = f"camara-{dep.get('id')}"
                    db.add(
                        RawLegislativeEvent(
                            source="camara_api",
                            entity_type="politician",
                            external_id=ext_id,
                            raw_payload=dep,
                        )
                    )
                    bronze_count += 1

                    party_acronym = (dep.get("siglaPartido") or "S.PART.").strip().upper()
                    camara_party_counts[party_acronym] += 1

                    party = _get_or_create_party(db, party_acronym)
                    existing = db.scalar(select(Politician).where(Politician.external_id == ext_id))
                    dep_id = dep.get("id")
                    portal_url = f"https://www.camara.leg.br/deputados/{dep_id}"
                    if existing:
                        existing.name = dep.get("nome", existing.name)
                        existing.state = dep.get("siglaUf", existing.state)
                        existing.party_id = party.id
                        existing.photo_url = dep.get("urlFoto") or existing.photo_url
                        existing.official_portal_url = portal_url
                        existing.is_active = True
                    else:
                        db.add(
                            Politician(
                                external_id=ext_id,
                                house_id=camara_house.id,
                                party_id=party.id,
                                name=dep.get("nome", "Deputado(a) Federal"),
                                state=dep.get("siglaUf", "BR"),
                                role="Deputado(a) Federal",
                                legislature="57ª Legislatura (2023–2027)",
                                attendance_rate="Dados sincronizados via Câmara dos Deputados",
                                biography_summary="Parlamentar em exercício sincronizado via API Dados Abertos da Câmara.",
                                photo_url=dep.get("urlFoto"),
                                official_portal_url=portal_url,
                                is_active=True,
                            )
                        )
                    upserted_count += 1

                if deputies:
                    camara_house.total_seats = len(deputies)
                    camara_house.party_composition_json = _build_composition_json(
                        camara_party_counts, db
                    )
                source_notes.append("camara_api:ok")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Câmara deputies sync fallback (%s)", exc)
                source_notes.append("camara_api:offline_fallback")

        # 2. Senado Federal Open Data API (all active senators)
        if senado_house:
            try:
                response = client.get(SENADO_SENATORS_URL, headers={"Accept": "application/json"})
                response.raise_for_status()
                payload = response.json()
                parlamentares = (
                    payload.get("ListaParlamentarEmExercicio", {})
                    .get("Parlamentares", {})
                    .get("Parlamentar", [])
                )
                if isinstance(parlamentares, dict):
                    parlamentares = [parlamentares]

                senado_party_counts: Counter[str] = Counter()
                for item in parlamentares:
                    ident = item.get("IdentificacaoParlamentar", {})
                    sen_code = ident.get("CodigoParlamentar")
                    if not sen_code:
                        continue
                    ext_id = f"senado-{sen_code}"
                    db.add(
                        RawLegislativeEvent(
                            source="senado_api",
                            entity_type="politician",
                            external_id=ext_id,
                            raw_payload=item,
                        )
                    )
                    bronze_count += 1

                    party_acronym = (
                        ident.get("SiglaPartidoParlamentar") or "S.PART."
                    ).strip().upper()
                    senado_party_counts[party_acronym] += 1

                    party = _get_or_create_party(db, party_acronym)
                    existing = db.scalar(select(Politician).where(Politician.external_id == ext_id))
                    portal_url = (
                        ident.get("UrlPaginaParlamentar")
                        or f"https://www25.senado.leg.br/web/senadores/senador/-/perfil/{sen_code}"
                    )
                    if existing:
                        existing.name = ident.get("NomeParlamentar", existing.name)
                        existing.state = ident.get("UfParlamentar", existing.state)
                        existing.party_id = party.id
                        existing.photo_url = ident.get("UrlFotoParlamentar") or existing.photo_url
                        existing.official_portal_url = portal_url
                        existing.is_active = True
                    else:
                        db.add(
                            Politician(
                                external_id=ext_id,
                                house_id=senado_house.id,
                                party_id=party.id,
                                name=ident.get("NomeParlamentar", "Senador(a)"),
                                state=ident.get("UfParlamentar", "BR"),
                                role="Senador(a) da República",
                                legislature="57ª Legislatura (2023–2031)",
                                attendance_rate="Dados sincronizados via Senado Federal",
                                biography_summary="Senador(a) em exercício sincronizado via API Dados Abertos do Senado.",
                                photo_url=ident.get("UrlFotoParlamentar"),
                                official_portal_url=portal_url,
                                is_active=True,
                            )
                        )
                    upserted_count += 1

                if senado_party_counts:
                    senado_house.total_seats = sum(senado_party_counts.values())
                    senado_house.party_composition_json = _build_composition_json(
                        senado_party_counts, db
                    )
                source_notes.append("senado_api:ok")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Senado sync fallback (%s)", exc)
                source_notes.append("senado_api:offline_fallback")

    db.commit()
    return {
        "task": "sync_politicians",
        "bronze_events_recorded": bronze_count,
        "records_upserted": upserted_count,
        "source_status": ", ".join(source_notes) or "completed",
    }


def poll_recent_bills(db: Session) -> dict[str, object]:
    """Track B (Near Real-Time Polling): Fetch recent PLs, store Bronze, and generate Desjuridiquês."""
    bronze_count = 0
    upserted_count = 0
    source_status = "camara_api:ok"

    camara_house = db.scalar(
        select(LegislativeHouse).where(LegislativeHouse.slug == "congresso-nacional")
    )
    if not camara_house:
        return {
            "task": "poll_recent_bills",
            "bronze_events_recorded": 0,
            "records_upserted": 0,
            "source_status": "missing_house_seed",
        }

    with httpx.Client(timeout=15.0) as client:
        try:
            response = client.get(CAMARA_BILLS_URL, headers={"Accept": "application/json"})
            response.raise_for_status()
            bills_data = response.json().get("dados", [])

            for item in bills_data:
                prop_id = item.get("id")
                if not prop_id:
                    continue
                ext_id = f"camara-pl-{prop_id}"
                db.add(
                    RawLegislativeEvent(
                        source="camara_api",
                        entity_type="bill",
                        external_id=ext_id,
                        raw_payload=item,
                    )
                )
                bronze_count += 1

                sigla = item.get("siglaTipo", "PL")
                numero = item.get("numero", prop_id)
                ano = int(item.get("ano", 2026))
                ementa = (item.get("ementa") or "").strip() or "Proposição legislativa em tramitação."
                bill_number = f"{sigla} {numero}/{ano}"
                title = ementa[:120] + ("..." if len(ementa) > 120 else "")

                existing = db.scalar(select(Bill).where(Bill.external_id == ext_id))
                if existing:
                    existing.official_summary = ementa
                    if not existing.desjuridiques_summary:
                        existing.desjuridiques_summary = generate_desjuridiques(title, ementa)
                else:
                    db.add(
                        Bill(
                            external_id=ext_id,
                            house_id=camara_house.id,
                            author_id=None,
                            number=bill_number,
                            year=ano,
                            title=title,
                            theme="Proposição Federal",
                            official_summary=ementa,
                            desjuridiques_summary=generate_desjuridiques(title, ementa),
                            status="Em Tramitação",
                            next_vote_at="Aguardando pauta em comissão",
                            is_urgent_vote=False,
                            likes_count=0,
                            votes_favor=0,
                            votes_against=0,
                            official_approval_rate=None,
                        )
                    )
                upserted_count += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("Câmara bills poll fallback (%s)", exc)
            source_status = "camara_api:offline_fallback"

    db.commit()
    return {
        "task": "poll_recent_bills",
        "bronze_events_recorded": bronze_count,
        "records_upserted": upserted_count,
        "source_status": source_status,
    }
