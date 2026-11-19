"""Quorum Medallion Lakehouse ETL Pipeline (Bronze -> Silver -> Gold).

Extracts legislative houses, bills, and citizen vote events from the Quorum
FastAPI backend (with automatic offline snapshot fallback), writes immutable
Bronze JSONL files, executes LGPD SHA-256 anonymization and deduplication into
Silver CSV tables, materializes Gold analytical metrics, and prints an
executive decision report in Brazilian Portuguese (pt-BR).
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent
LAKEHOUSE_DIR = BASE_DIR / "lakehouse"
BRONZE_DIR = LAKEHOUSE_DIR / "bronze"
SILVER_DIR = LAKEHOUSE_DIR / "silver"
GOLD_DIR = LAKEHOUSE_DIR / "gold"

API_BASE_URL = os.getenv("QUORUM_API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")
LGPD_HASH_SALT = os.getenv("QUORUM_LGPD_SALT", "quorum-fiap-gs2-2026-lgpd")
API_TIMEOUT_SECONDS = 2.0


@dataclass(frozen=True)
class ExtractionPayload:
    """Container holding raw Bronze inputs and provenance metadata."""

    ingestion_mode: str
    houses: list[dict[str, Any]]
    bills: list[dict[str, Any]]
    raw_vote_events: list[dict[str, Any]]
    overview: dict[str, Any] | None = None


def ensure_lakehouse_directories() -> None:
    """Create Bronze, Silver, and Gold lakehouse directories if absent."""
    for directory in (BRONZE_DIR, SILVER_DIR, GOLD_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def anonymize_citizen_token(raw_identifier: str) -> str:
    """Compute an irreversible SHA-256 pseudonym per LGPD Art. 5 / Art. 7."""
    material = f"{LGPD_HASH_SALT}:{raw_identifier.strip().lower()}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def fetch_json(endpoint: str) -> Any:
    """Perform a short-timeout HTTP GET against the Quorum FastAPI backend."""
    url = f"{API_BASE_URL}{endpoint}"
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "Quorum-BigData-ETL/1.0"},
    )
    with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
        if response.status != 200:
            raise RuntimeError(f"Unexpected HTTP status {response.status} for {url}")
        return json.loads(response.read().decode("utf-8"))


def build_offline_snapshot() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return realistic Brazilian legislative houses and bills for resilient fallback."""
    houses: list[dict[str, Any]] = [
        {
            "id": 1,
            "slug": "camara-dos-deputados",
            "name": "Câmara dos Deputados",
            "short_name": "Câmara Federal",
            "level": "Federal",
            "total_seats": 513,
            "party_composition": [
                {"party": "PL", "party_name": "Partido Liberal", "seat_count": 99, "color_hex": "#1D4ED8"},
                {"party": "PT", "party_name": "Partido dos Trabalhadores", "seat_count": 68, "color_hex": "#DC2626"},
                {"party": "UNIÃO", "party_name": "União Brasil", "seat_count": 59, "color_hex": "#0284C7"},
                {"party": "PP", "party_name": "Progressistas", "seat_count": 50, "color_hex": "#2563EB"},
                {"party": "MDB", "party_name": "Movimento Democrático Brasileiro", "seat_count": 44, "color_hex": "#16A34A"},
                {"party": "PSD", "party_name": "Partido Social Democrático", "seat_count": 44, "color_hex": "#D97706"},
                {"party": "REPUBLICANOS", "party_name": "Republicanos", "seat_count": 41, "color_hex": "#0D9488"},
                {"party": "Outros", "party_name": "Demais Bancadas", "seat_count": 108, "color_hex": "#64748B"},
            ],
        },
        {
            "id": 2,
            "slug": "senado-federal",
            "name": "Senado Federal",
            "short_name": "Senado Federal",
            "level": "Federal",
            "total_seats": 81,
            "party_composition": [
                {"party": "PSD", "party_name": "Partido Social Democrático", "seat_count": 15, "color_hex": "#D97706"},
                {"party": "PL", "party_name": "Partido Liberal", "seat_count": 14, "color_hex": "#1D4ED8"},
                {"party": "MDB", "party_name": "Movimento Democrático Brasileiro", "seat_count": 11, "color_hex": "#16A34A"},
                {"party": "PT", "party_name": "Partido dos Trabalhadores", "seat_count": 9, "color_hex": "#DC2626"},
                {"party": "UNIÃO", "party_name": "União Brasil", "seat_count": 7, "color_hex": "#0284C7"},
                {"party": "PP", "party_name": "Progressistas", "seat_count": 6, "color_hex": "#2563EB"},
                {"party": "Outros", "party_name": "Demais Bancadas", "seat_count": 19, "color_hex": "#64748B"},
            ],
        },
        {
            "id": 3,
            "slug": "alesp-sp",
            "name": "Assembleia Legislativa de São Paulo",
            "short_name": "ALESP",
            "level": "Estadual",
            "total_seats": 94,
            "party_composition": [
                {"party": "PL", "party_name": "Partido Liberal", "seat_count": 19, "color_hex": "#1D4ED8"},
                {"party": "PT", "party_name": "Partido dos Trabalhadores", "seat_count": 18, "color_hex": "#DC2626"},
                {"party": "PSDB", "party_name": "Partido da Social Democracia Brasileira", "seat_count": 9, "color_hex": "#0EA5E9"},
                {"party": "REPUBLICANOS", "party_name": "Republicanos", "seat_count": 8, "color_hex": "#0D9488"},
                {"party": "UNIÃO", "party_name": "União Brasil", "seat_count": 8, "color_hex": "#0284C7"},
                {"party": "MDB", "party_name": "Movimento Democrático Brasileiro", "seat_count": 7, "color_hex": "#16A34A"},
                {"party": "Outros", "party_name": "Demais Bancadas", "seat_count": 25, "color_hex": "#64748B"},
            ],
        },
        {
            "id": 4,
            "slug": "camara-sp",
            "name": "Câmara Municipal de São Paulo",
            "short_name": "CMSP",
            "level": "Municipal",
            "total_seats": 55,
            "party_composition": [
                {"party": "MDB", "party_name": "Movimento Democrático Brasileiro", "seat_count": 7, "color_hex": "#16A34A"},
                {"party": "PL", "party_name": "Partido Liberal", "seat_count": 7, "color_hex": "#1D4ED8"},
                {"party": "PT", "party_name": "Partido dos Trabalhadores", "seat_count": 8, "color_hex": "#DC2626"},
                {"party": "UNIÃO", "party_name": "União Brasil", "seat_count": 7, "color_hex": "#0284C7"},
                {"party": "PSOL", "party_name": "Partido Socialismo e Liberdade", "seat_count": 6, "color_hex": "#EAB308"},
                {"party": "PSD", "party_name": "Partido Social Democrático", "seat_count": 6, "color_hex": "#D97706"},
                {"party": "Outros", "party_name": "Demais Bancadas", "seat_count": 14, "color_hex": "#64748B"},
            ],
        },
    ]

    bills: list[dict[str, Any]] = [
        {
            "id": 101,
            "external_id": "senado-pl-2338-2023",
            "number": "PL 2338/2023",
            "year": 2023,
            "title": "Marco Legal da Inteligência Artificial no Brasil",
            "theme": "Tecnologia e Direitos Digitais",
            "house_slug": "senado-federal",
            "house_short_name": "Senado Federal",
            "status": "Em Tramitação",
            "votes_favor": 1840,
            "votes_against": 360,
            "official_approval_rate": 72,
        },
        {
            "id": 102,
            "external_id": "camara-plp-68-2024",
            "number": "PLP 68/2024",
            "year": 2024,
            "title": "Regulamentação da Reforma Tributária (IBS, CBS e Cashback)",
            "theme": "Economia e Tributação",
            "house_slug": "camara-dos-deputados",
            "house_short_name": "Câmara Federal",
            "status": "Aprovado",
            "votes_favor": 2410,
            "votes_against": 1190,
            "official_approval_rate": 74,
        },
        {
            "id": 103,
            "external_id": "camara-pl-2628-2022",
            "number": "PL 2628/2022",
            "year": 2022,
            "title": "Proteção de Crianças e Adolescentes em Ambientes Digitais",
            "theme": "Educação e Cidadania Digital",
            "house_slug": "camara-dos-deputados",
            "house_short_name": "Câmara Federal",
            "status": "Votação Agendada",
            "votes_favor": 3120,
            "votes_against": 210,
            "official_approval_rate": 88,
        },
        {
            "id": 104,
            "external_id": "alesp-pl-412-2025",
            "number": "PL 412/2025",
            "year": 2025,
            "title": "Incentivo à Geração Solar em Escolas Públicas Paulistas",
            "theme": "Energia Limpa",
            "house_slug": "alesp-sp",
            "house_short_name": "ALESP",
            "status": "Votação Agendada",
            "votes_favor": 980,
            "votes_against": 140,
            "official_approval_rate": 81,
        },
        {
            "id": 105,
            "external_id": "cmsp-pl-118-2025",
            "number": "PL 118/2025",
            "year": 2025,
            "title": "Expansão de Corredores Verdes e Totens de Participação Cívica",
            "theme": "Mobilidade e Cidade Sustentável",
            "house_slug": "camara-sp",
            "house_short_name": "CMSP",
            "status": "Aprovado",
            "votes_favor": 760,
            "votes_against": 240,
            "official_approval_rate": 78,
        },
        {
            "id": 106,
            "external_id": "camara-pec-18-2025",
            "number": "PEC 18/2025",
            "year": 2025,
            "title": "Reorganização de Fundos Paritários sem Quórum de Audiência",
            "theme": "Administração Pública",
            "house_slug": "camara-dos-deputados",
            "house_short_name": "Câmara Federal",
            "status": "Em Tramitação",
            "votes_favor": 410,
            "votes_against": 1590,
            "official_approval_rate": 76,
        },
    ]
    return houses, bills


def build_raw_citizen_vote_stream(
    bills: list[dict[str, Any]],
    overview: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Generate a compact raw omnichannel vote event stream for Bronze -> Silver audit.

    Includes two intentional duplicate voter tokens so Silver deduplication and
    LGPD SHA-256 anonymization can be verified deterministically.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    raw_events: list[dict[str, Any]] = []
    target_bills = bills[:6]

    web_bias = 0.65
    if overview:
        total_audit = (overview.get("web_votes") or 0) + (overview.get("iot_totem_votes") or 0)
        if total_audit > 0:
            web_bias = (overview.get("web_votes") or 0) / total_audit

    sample_tokens = [
        ("cpf-hash-seed-001", "favor", "web"),
        ("totem-metro-se-014", "favor", "iot_totem"),
        ("cidadao-sp-092@example.br", "against", "web"),
        ("totem-estacao-luz-008", "favor", "iot_totem"),
    ]

    for idx, bill in enumerate(target_bills):
        ext_id = str(bill.get("external_id") or f"bill-{bill.get('id', idx)}")
        token_a, choice_a, _ = sample_tokens[idx % len(sample_tokens)]
        raw_events.append(
            {
                "event_id": f"evt-{idx}-a",
                "bill_external_id": ext_id,
                "raw_voter_token": f"{token_a}-{idx}",
                "choice": choice_a,
                "source": "web" if web_bias >= 0.5 else "iot_totem",
                "captured_at": now_iso,
            }
        )
        if idx < 4:
            raw_events.append(
                {
                    "event_id": f"evt-{idx}-b",
                    "bill_external_id": ext_id,
                    "raw_voter_token": f"totem-terminal-b-{idx}",
                    "choice": "favor" if (bill.get("votes_favor", 1) >= bill.get("votes_against", 0)) else "against",
                    "source": "iot_totem" if idx % 2 == 0 else "web",
                    "captured_at": now_iso,
                }
            )

    # Intentional duplicate events to prove Bronze -> Silver deduplication.
    if target_bills:
        first_bill_ext = str(target_bills[0].get("external_id") or f"bill-{target_bills[0].get('id', 0)}")
        raw_events.append(
            {
                "event_id": "evt-dup-001",
                "bill_external_id": first_bill_ext,
                "raw_voter_token": f"{sample_tokens[0][0]}-0",
                "choice": sample_tokens[0][1],
                "source": "web",
                "captured_at": now_iso,
            }
        )
        raw_events.append(
            {
                "event_id": "evt-dup-002",
                "bill_external_id": first_bill_ext,
                "raw_voter_token": "totem-terminal-b-0",
                "choice": "favor",
                "source": "iot_totem",
                "captured_at": now_iso,
            }
        )

    return raw_events


def extract_bronze_inputs() -> ExtractionPayload:
    """Attempt live extraction from FastAPI; fall back smoothly if unavailable."""
    try:
        houses = fetch_json("/houses")
        bills = fetch_json("/bills")
        overview = fetch_json("/dashboard/overview?house_slug=all")
        if not isinstance(houses, list) or not isinstance(bills, list) or not houses or not bills:
            raise ValueError("Empty API payload received from FastAPI")
        raw_votes = build_raw_citizen_vote_stream(bills, overview if isinstance(overview, dict) else None)
        return ExtractionPayload(
            ingestion_mode=f"API FastAPI ao vivo ({API_BASE_URL})",
            houses=houses,
            bills=bills,
            raw_vote_events=raw_votes,
            overview=overview if isinstance(overview, dict) else None,
        )
    except Exception as exc:
        houses, bills = build_offline_snapshot()
        raw_votes = build_raw_citizen_vote_stream(bills, None)
        reason = type(exc).__name__
        return ExtractionPayload(
            ingestion_mode=f"Snapshot Offline Resiliente (API indisponível: {reason})",
            houses=houses,
            bills=bills,
            raw_vote_events=raw_votes,
            overview=None,
        )


def write_bronze_jsonl(path: Path, records: list[dict[str, Any]], source_label: str) -> None:
    """Persist immutable Bronze records as compact one-object-per-line JSONL."""
    ingested_at = datetime.now(timezone.utc).isoformat()
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            envelope = {
                "ingested_at": ingested_at,
                "source_system": source_label,
                "payload": record,
            }
            handle.write(json.dumps(envelope, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_bronze_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read Bronze JSONL envelopes back for decoupled Silver transformation."""
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def run_bronze_stage(payload: ExtractionPayload) -> dict[str, Path]:
    """Step 1: Persist raw API/event payloads into Bronze JSONL files."""
    houses_path = BRONZE_DIR / "raw_legislative_houses.jsonl"
    bills_path = BRONZE_DIR / "raw_legislative_bills.jsonl"
    votes_path = BRONZE_DIR / "raw_citizen_votes.jsonl"

    write_bronze_jsonl(houses_path, payload.houses, payload.ingestion_mode)
    write_bronze_jsonl(bills_path, payload.bills, payload.ingestion_mode)
    write_bronze_jsonl(votes_path, payload.raw_vote_events, "quorum_omnichannel_stream")

    return {"houses": houses_path, "bills": bills_path, "votes": votes_path}


def run_silver_stage(bronze_paths: dict[str, Path]) -> dict[str, Any]:
    """Step 2: Clean, normalize, deduplicate, and SHA-256 anonymize into Silver CSVs."""
    raw_houses = read_bronze_jsonl(bronze_paths["houses"])
    raw_bills = read_bronze_jsonl(bronze_paths["bills"])
    raw_votes = read_bronze_jsonl(bronze_paths["votes"])

    # Normalize house party compositions
    houses_parties_path = SILVER_DIR / "houses_parties.csv"
    seen_house_party: set[tuple[str, str]] = set()
    house_party_rows: list[dict[str, Any]] = []
    for envelope in raw_houses:
        h = envelope["payload"]
        slug = str(h.get("slug") or h.get("id"))
        short_name = str(h.get("short_name") or h.get("name") or slug)
        sphere = str(h.get("level") or h.get("sphere") or "Federal")
        total_seats = max(int(h.get("total_seats") or 0), 1)
        for item in h.get("party_composition", []):
            acronym = str(item.get("party") or item.get("party_acronym") or "Outros").strip()
            key = (slug, acronym)
            if key in seen_house_party:
                continue
            seen_house_party.add(key)
            seat_count = max(int(item.get("seat_count") or item.get("seats") or 0), 0)
            house_party_rows.append(
                {
                    "house_slug": slug,
                    "house_short_name": short_name,
                    "level": sphere,
                    "total_seats": total_seats,
                    "party_acronym": acronym,
                    "party_name": str(item.get("party_name") or acronym),
                    "seat_count": seat_count,
                    "seat_share_pct": round((seat_count / total_seats) * 100.0, 2),
                    "color_hex": str(item.get("color_hex") or "#64748B"),
                }
            )

    with houses_parties_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "house_slug",
            "house_short_name",
            "level",
            "total_seats",
            "party_acronym",
            "party_name",
            "seat_count",
            "seat_share_pct",
            "color_hex",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(house_party_rows)

    # Normalize legislative bills
    bills_path = SILVER_DIR / "bills_normalized.csv"
    seen_bills: set[str] = set()
    bill_rows: list[dict[str, Any]] = []
    for envelope in raw_bills:
        b = envelope["payload"]
        ext_id = str(b.get("external_id") or f"bill-{b.get('id')}")
        if ext_id in seen_bills:
            continue
        seen_bills.add(ext_id)
        favor = max(int(b.get("votes_favor") or 0), 0)
        against = max(int(b.get("votes_against") or 0), 0)
        total_votes = favor + against
        citizen_favor_pct = round((favor / total_votes) * 100.0, 2) if total_votes > 0 else 0.0
        official_pct = float(b.get("official_approval_rate") or 0.0)
        bill_rows.append(
            {
                "bill_external_id": ext_id,
                "number": str(b.get("number") or ""),
                "year": int(b.get("year") or 2026),
                "title": str(b.get("title") or "").strip(),
                "theme": str(b.get("theme") or "Geral").strip(),
                "house_slug": str(b.get("house_slug") or ""),
                "house_short_name": str(b.get("house_short_name") or ""),
                "status": str(b.get("status") or "Em Tramitação"),
                "votes_favor": favor,
                "votes_against": against,
                "total_citizen_votes": total_votes,
                "citizen_favor_pct": citizen_favor_pct,
                "official_approval_pct": round(official_pct, 2),
            }
        )

    with bills_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "bill_external_id",
            "number",
            "year",
            "title",
            "theme",
            "house_slug",
            "house_short_name",
            "status",
            "votes_favor",
            "votes_against",
            "total_citizen_votes",
            "citizen_favor_pct",
            "official_approval_pct",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(bill_rows)

    # Anonymize (SHA-256) and deduplicate raw citizen vote events
    votes_path = SILVER_DIR / "citizen_votes_anonymized.csv"
    dedup_keys: set[tuple[str, str]] = set()
    clean_votes: list[dict[str, Any]] = []
    duplicate_count = 0

    for envelope in raw_votes:
        v = envelope["payload"]
        bill_ext = str(v.get("bill_external_id") or "")
        raw_token = str(v.get("raw_voter_token") or "")
        citizen_hash = anonymize_citizen_token(raw_token)
        dedup_key = (bill_ext, citizen_hash)
        if dedup_key in dedup_keys:
            duplicate_count += 1
            continue
        dedup_keys.add(dedup_key)
        clean_votes.append(
            {
                "bill_external_id": bill_ext,
                "citizen_hash": citizen_hash,
                "choice": "favor" if str(v.get("choice")).lower() == "favor" else "against",
                "source": "iot_totem" if str(v.get("source")).lower() == "iot_totem" else "web",
                "captured_at": str(v.get("captured_at") or ""),
            }
        )

    with votes_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["bill_external_id", "citizen_hash", "choice", "source", "captured_at"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_votes)

    return {
        "houses_parties_path": houses_parties_path,
        "bills_path": bills_path,
        "votes_path": votes_path,
        "raw_vote_events_count": len(raw_votes),
        "deduplicated_vote_events_count": len(clean_votes),
        "duplicates_removed": duplicate_count,
    }


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    """Load CSV rows cleanly using UTF-8."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def classify_convergence(score: float) -> str:
    """Map numeric convergence score to an executive alignment band in pt-BR."""
    if score >= 80.0:
        return "Alta Convergência"
    if score >= 50.0:
        return "Convergência Moderada"
    return "Desalinhamento Crítico"


def run_gold_stage(silver_info: dict[str, Any], ingestion_mode: str) -> dict[str, Any]:
    """Step 3: Aggregate Silver CSVs into Gold business metrics and summary JSON."""
    house_party_rows = read_csv_rows(silver_info["houses_parties_path"])
    bill_rows = read_csv_rows(silver_info["bills_path"])
    vote_rows = read_csv_rows(silver_info["votes_path"])

    # Compute Party Fragmentation (Normalized HHI & ENP) per house
    by_house_parties: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in house_party_rows:
        by_house_parties[row["house_slug"]].append(row)

    house_hhi_map: dict[str, tuple[float, float]] = {}
    gold_party_rows: list[dict[str, Any]] = []
    for slug, items in by_house_parties.items():
        total_seats = max(int(items[0]["total_seats"]), 1)
        sum_sq = sum((int(item["seat_count"]) / total_seats) ** 2 for item in items)
        hhi_norm = round((1.0 - sum_sq) * 100.0, 2)
        enp = round(1.0 / sum_sq, 2) if sum_sq > 0 else 0.0
        house_hhi_map[slug] = (hhi_norm, enp)
        for item in items:
            gold_party_rows.append(
                {
                    "house_slug": slug,
                    "house_short_name": item["house_short_name"],
                    "level": item["level"],
                    "total_seats": total_seats,
                    "party_acronym": item["party_acronym"],
                    "seat_count": int(item["seat_count"]),
                    "seat_share_pct": float(item["seat_share_pct"]),
                    "house_fragmentation_hhi": hhi_norm,
                    "effective_parties_enp": enp,
                }
            )

    gold_party_path = GOLD_DIR / "party_seat_composition.csv"
    with gold_party_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "house_slug",
            "house_short_name",
            "level",
            "total_seats",
            "party_acronym",
            "seat_count",
            "seat_share_pct",
            "house_fragmentation_hhi",
            "effective_parties_enp",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(gold_party_rows)

    # Omnichannel channel counts per bill from anonymized Silver vote log
    channel_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"web": 0, "iot_totem": 0})
    for vote in vote_rows:
        channel_counts[vote["bill_external_id"]][vote["source"]] += 1

    # Compute bill-level convergence metrics
    gold_bill_rows: list[dict[str, Any]] = []
    for b in bill_rows:
        ext_id = b["bill_external_id"]
        citizen_pct = float(b["citizen_favor_pct"])
        official_pct = float(b["official_approval_pct"])
        convergence_index = round(max(0.0, 100.0 - abs(citizen_pct - official_pct)), 2)
        web_cnt = channel_counts[ext_id]["web"]
        iot_cnt = channel_counts[ext_id]["iot_totem"]
        audit_total = web_cnt + iot_cnt
        iot_share_pct = round((iot_cnt / audit_total) * 100.0, 2) if audit_total > 0 else 0.0

        gold_bill_rows.append(
            {
                "bill_external_id": ext_id,
                "number": b["number"],
                "title": b["title"],
                "house_slug": b["house_slug"],
                "house_short_name": b["house_short_name"],
                "status": b["status"],
                "total_citizen_votes": int(b["total_citizen_votes"]),
                "citizen_favor_pct": citizen_pct,
                "official_approval_pct": official_pct,
                "convergence_index": convergence_index,
                "alignment_classification": classify_convergence(convergence_index),
                "web_votes_audited": web_cnt,
                "iot_totem_votes_audited": iot_cnt,
                "iot_share_pct": iot_share_pct,
            }
        )

    gold_bills_path = GOLD_DIR / "bill_convergence_metrics.csv"
    with gold_bills_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "bill_external_id",
            "number",
            "title",
            "house_slug",
            "house_short_name",
            "status",
            "total_citizen_votes",
            "citizen_favor_pct",
            "official_approval_pct",
            "convergence_index",
            "alignment_classification",
            "web_votes_audited",
            "iot_totem_votes_audited",
            "iot_share_pct",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(gold_bill_rows)

    # Aggregate Executive KPIs per Legislative House
    bills_by_house: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in gold_bill_rows:
        bills_by_house[row["house_slug"]].append(row)

    gold_house_rows: list[dict[str, Any]] = []
    for slug, items in by_house_parties.items():
        h_bills = bills_by_house.get(slug, [])
        hhi_norm, enp = house_hhi_map[slug]
        monitored_cnt = len(h_bills)
        approved_cnt = sum(1 for item in h_bills if item["status"] == "Aprovado")
        total_votes = sum(item["total_citizen_votes"] for item in h_bills)
        avg_favor = round(sum(item["citizen_favor_pct"] for item in h_bills) / monitored_cnt, 2) if monitored_cnt else 0.0
        avg_official = round(sum(item["official_approval_pct"] for item in h_bills) / monitored_cnt, 2) if monitored_cnt else 0.0
        avg_conv = round(sum(item["convergence_index"] for item in h_bills) / monitored_cnt, 2) if monitored_cnt else 0.0
        web_tot = sum(item["web_votes_audited"] for item in h_bills)
        iot_tot = sum(item["iot_totem_votes_audited"] for item in h_bills)
        iot_pct = round((iot_tot / (web_tot + iot_tot)) * 100.0, 2) if (web_tot + iot_tot) > 0 else 0.0

        gold_house_rows.append(
            {
                "house_slug": slug,
                "house_short_name": items[0]["house_short_name"],
                "level": items[0]["level"],
                "total_seats": int(items[0]["total_seats"]),
                "monitored_bills_count": monitored_cnt,
                "approved_bills_count": approved_cnt,
                "total_citizen_votes": total_votes,
                "avg_citizen_favor_pct": avg_favor,
                "avg_official_approval_pct": avg_official,
                "avg_convergence_index": avg_conv,
                "party_fragmentation_hhi": hhi_norm,
                "effective_parties_enp": enp,
                "web_votes_audited": web_tot,
                "iot_totem_votes_audited": iot_tot,
                "iot_share_pct": iot_pct,
            }
        )

    gold_houses_path = GOLD_DIR / "house_kpis.csv"
    with gold_houses_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "house_slug",
            "house_short_name",
            "level",
            "total_seats",
            "monitored_bills_count",
            "approved_bills_count",
            "total_citizen_votes",
            "avg_citizen_favor_pct",
            "avg_official_approval_pct",
            "avg_convergence_index",
            "party_fragmentation_hhi",
            "effective_parties_enp",
            "web_votes_audited",
            "iot_totem_votes_audited",
            "iot_share_pct",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(gold_house_rows)

    total_audit_web = sum(item["web_votes_audited"] for item in gold_bill_rows)
    total_audit_iot = sum(item["iot_totem_votes_audited"] for item in gold_bill_rows)
    global_iot_pct = (
        round((total_audit_iot / (total_audit_web + total_audit_iot)) * 100.0, 2)
        if (total_audit_web + total_audit_iot) > 0
        else 0.0
    )
    global_avg_conv = (
        round(sum(item["convergence_index"] for item in gold_bill_rows) / len(gold_bill_rows), 2)
        if gold_bill_rows
        else 0.0
    )

    sorted_bills = sorted(gold_bill_rows, key=lambda item: item["convergence_index"], reverse=True)
    top_bill = sorted_bills[0] if sorted_bills else None
    lowest_bill = sorted_bills[-1] if sorted_bills else None

    persisted_summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ingestion_mode": ingestion_mode,
        "lgpd_anonymization": "SHA-256 irreversível (64 hexadecimais, zero PII em Silver/Gold)",
        "bronze_raw_vote_events": silver_info["raw_vote_events_count"],
        "silver_deduplicated_vote_events": silver_info["deduplicated_vote_events_count"],
        "duplicates_removed": silver_info["duplicates_removed"],
        "total_houses": len(gold_house_rows),
        "total_bills": len(gold_bill_rows),
        "global_avg_convergence_index": global_avg_conv,
        "omnichannel_web_votes_audited": total_audit_web,
        "omnichannel_iot_votes_audited": total_audit_iot,
        "omnichannel_iot_share_pct": global_iot_pct,
        "highest_convergence_bill": (
            {
                "number": top_bill["number"],
                "convergence_index": top_bill["convergence_index"],
                "classification": top_bill["alignment_classification"],
            }
            if top_bill
            else None
        ),
        "lowest_convergence_bill": (
            {
                "number": lowest_bill["number"],
                "convergence_index": lowest_bill["convergence_index"],
                "classification": lowest_bill["alignment_classification"],
            }
            if lowest_bill
            else None
        ),
    }

    summary_path = GOLD_DIR / "gold_summary.json"
    summary_path.write_text(
        json.dumps(persisted_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        **persisted_summary,
        "gold_bills": gold_bill_rows,
        "gold_houses": gold_house_rows,
    }


def compute_lakehouse_footprint_bytes() -> int:
    """Calculate total disk footprint of generated Lakehouse artifacts."""
    return sum(p.stat().st_size for p in LAKEHOUSE_DIR.rglob("*") if p.is_file())


def print_decision_report(summary: dict[str, Any], footprint_bytes: int) -> None:
    """Print structured analytical executive summary in Brazilian Portuguese (pt-BR)."""
    print("=" * 78)
    print("QUORUM LAKEHOUSE — RELATÓRIO ANALÍTICO MEDALLION (BRONZE -> SILVER -> GOLD)")
    print("=" * 78)
    print(f"Fonte de Ingestão : {summary['ingestion_mode']}")
    print(f"Governança LGPD   : {summary['lgpd_anonymization']}")
    print(
        f"Saneamento Votos  : {summary['bronze_raw_vote_events']} brutos (Bronze) -> "
        f"{summary['silver_deduplicated_vote_events']} deduplicados (Silver) "
        f"[{summary['duplicates_removed']} duplicatas bloqueadas]"
    )
    print(
        f"Canal Omnichannel : Web {100.0 - summary['omnichannel_iot_share_pct']:.1f}% "
        f"({summary['omnichannel_web_votes_audited']} eventos) | "
        f"Totem IoT {summary['omnichannel_iot_share_pct']:.1f}% "
        f"({summary['omnichannel_iot_votes_audited']} eventos)"
    )
    print(f"Convergência Média: {summary['global_avg_convergence_index']:.2f}% ({len(summary['gold_bills'])} proposições)")
    print("-" * 78)
    print("INDICADORES EXECUTIVOS POR CASA LEGISLATIVA (CAMADA GOLD):")
    for house in summary["gold_houses"]:
        print(
            f"  • {house['house_short_name']:<16} | Esfera: {house['level']:<9} | "
            f"Cadeiras: {house['total_seats']:>3} | HHI Frag.: {house['party_fragmentation_hhi']:>5.1f}% "
            f"(ENP {house['effective_parties_enp']:>4.1f}) | "
            f"Convergência: {house['avg_convergence_index']:>5.1f}%"
        )
    print("-" * 78)
    print("ÍNDICE DE CONVERGÊNCIA POR PROPOSIÇÃO (CIDADÃO VS. PARLAMENTO):")
    sorted_bills = sorted(summary["gold_bills"], key=lambda item: item["convergence_index"], reverse=True)
    for bill in sorted_bills:
        print(
            f"  • {bill['number']:<14} ({bill['house_short_name']:<14}) | "
            f"Cidadão: {bill['citizen_favor_pct']:>5.1f}% | Oficial: {bill['official_approval_pct']:>5.1f}% | "
            f"Convergência: {bill['convergence_index']:>5.1f}% [{bill['alignment_classification']}]"
        )
    print("-" * 78)
    print(f"Artefatos gerados em ./lakehouse ({footprint_bytes / 1024:.2f} KB no total)")
    print("=" * 78)


def main() -> int:
    """Run Bronze -> Silver -> Gold Lakehouse ETL pipeline."""
    ensure_lakehouse_directories()
    payload = extract_bronze_inputs()
    bronze_paths = run_bronze_stage(payload)
    silver_info = run_silver_stage(bronze_paths)
    summary = run_gold_stage(silver_info, payload.ingestion_mode)
    footprint_bytes = compute_lakehouse_footprint_bytes()
    print_decision_report(summary, footprint_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
