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
    "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome&itens=30"
)
SENADO_SENATORS_URL = "https://legis.senado.leg.br/dadosabertos/senador/lista/atual"
CAMARA_BILLS_URL = (
    "https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PL&itens=15&ordem=DESC&ordenarPor=id"
)


def _get_or_create_party(db: Session, acronym: str) -> Party:
    normalized = (acronym or "SEM PARTIDO").strip().upper()
    party = db.scalar(select(Party).where(Party.acronym == normalized))
    if party:
        return party
    party = Party(
        acronym=normalized,
        name=normalized,
        color_hex="#64748B",
        spectrum="Diversos",
        program_summary="Dados sincronizados automaticamente via API oficial do Legislativo.",
        official_portal_url="https://www.tse.jus.br/partidos/partidos-registrados-no-tse",
    )
    db.add(party)
    db.flush()
    return party


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

    with httpx.Client(timeout=15.0) as client:
        # 1. Câmara dos Deputados Open Data API
        if camara_house:
            try:
                response = client.get(CAMARA_DEPUTIES_URL, headers={"Accept": "application/json"})
                response.raise_for_status()
                payload = response.json()
                deputies = payload.get("dados", [])
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

                    party = _get_or_create_party(db, dep.get("siglaPartido", ""))
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
                                attendance_rate="Dados em sincronização oficial",
                                biography_summary="Parlamentar em exercício sincronizado via Câmara dos Deputados.",
                                photo_url=dep.get("urlFoto"),
                                official_portal_url=portal_url,
                                is_active=True,
                            )
                        )
                    upserted_count += 1
                source_notes.append("camara_api:ok")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Câmara deputies sync fallback (%s)", exc)
                source_notes.append("camara_api:offline_fallback")

        # 2. Senado Federal Open Data API
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
                for item in parlamentares[:30]:
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

                    party = _get_or_create_party(db, ident.get("SiglaPartidoParlamentar", ""))
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
                                attendance_rate="Dados em sincronização oficial",
                                biography_summary="Senador(a) em exercício sincronizado via Senado Federal.",
                                photo_url=ident.get("UrlFotoParlamentar"),
                                official_portal_url=portal_url,
                                is_active=True,
                            )
                        )
                    upserted_count += 1
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
