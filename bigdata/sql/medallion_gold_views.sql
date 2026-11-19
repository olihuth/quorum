-- =============================================================================
-- Quorum Platform — Medallion Gold Analytical Views (PostgreSQL 16)
-- Reads normalized Silver tables and immutable Bronze JSONB events to power
-- the Panorama Legislativo dashboard and BI consumers.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Party Seat Composition & Herfindahl-Hirschman Fragmentation (per House)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold_party_seat_composition AS
WITH exploded_composition AS (
    SELECT
        lh.id AS house_id,
        lh.slug AS house_slug,
        lh.short_name AS house_short_name,
        lh.level AS level,
        lh.total_seats AS total_seats,
        COALESCE(elem->>'party', 'N/A') AS party_acronym,
        COALESCE(elem->>'party_name', elem->>'party', 'Unknown') AS party_name,
        COALESCE((elem->>'seat_count')::integer, 0) AS seat_count,
        COALESCE(elem->>'color_hex', '#64748B') AS color_hex
    FROM legislative_houses lh
    CROSS JOIN LATERAL jsonb_array_elements(
        COALESCE(lh.party_composition_json, '[]'::jsonb)
    ) AS elem
),
house_hhi AS (
    SELECT
        house_id,
        ROUND(
            (
                1.0::numeric - COALESCE(
                    SUM(
                        POWER(
                            seat_count::numeric / NULLIF(total_seats, 0)::numeric,
                            2
                        )
                    ),
                    0::numeric
                )
            ) * 100.0,
            2
        ) AS house_fragmentation_index,
        ROUND(
            1.0::numeric / NULLIF(
                SUM(
                    POWER(
                        seat_count::numeric / NULLIF(total_seats, 0)::numeric,
                        2
                    )
                ),
                0::numeric
            ),
            2
        ) AS effective_number_of_parties
    FROM exploded_composition
    GROUP BY house_id
)
SELECT
    ec.house_id,
    ec.house_slug,
    ec.house_short_name,
    ec.level,
    ec.total_seats,
    ec.party_acronym,
    ec.party_name,
    ec.color_hex,
    ec.seat_count,
    ROUND(
        (ec.seat_count::numeric / NULLIF(ec.total_seats, 0)::numeric) * 100.0,
        2
    ) AS seat_share_pct,
    COALESCE(hh.house_fragmentation_index, 0::numeric) AS house_fragmentation_index,
    COALESCE(hh.effective_number_of_parties, 0::numeric) AS effective_number_of_parties
FROM exploded_composition ec
LEFT JOIN house_hhi hh ON hh.house_id = ec.house_id;


-- -----------------------------------------------------------------------------
-- 2. Bill-Level Citizen vs. Official Convergence & Omnichannel Audit
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold_bill_convergence_metrics AS
WITH vote_channel_stats AS (
    SELECT
        cv.bill_id,
        COUNT(cv.id) AS audited_citizen_votes,
        COUNT(cv.id) FILTER (WHERE cv.source = 'web') AS web_votes_count,
        COUNT(cv.id) FILTER (WHERE cv.source = 'iot_totem') AS iot_totem_votes_count,
        COUNT(cv.id) FILTER (WHERE cv.choice = 'favor') AS audited_favor_votes,
        COUNT(cv.id) FILTER (WHERE cv.choice = 'against') AS audited_against_votes
    FROM citizen_votes cv
    GROUP BY cv.bill_id
),
bill_base AS (
    SELECT
        b.id AS bill_id,
        b.external_id AS bill_external_id,
        b.number AS bill_number,
        b.year AS bill_year,
        b.title AS bill_title,
        b.theme AS theme,
        b.status AS status,
        b.is_urgent_vote AS is_urgent_vote,
        lh.id AS house_id,
        lh.slug AS house_slug,
        lh.short_name AS house_short_name,
        lh.level AS level,
        COALESCE(p.name, 'Bancada / Comissão') AS author_name,
        b.votes_favor AS votes_favor,
        b.votes_against AS votes_against,
        (b.votes_favor + b.votes_against) AS total_citizen_votes,
        ROUND(
            (
                b.votes_favor::numeric
                / NULLIF(b.votes_favor + b.votes_against, 0)::numeric
            ) * 100.0,
            2
        ) AS citizen_favor_pct,
        COALESCE(b.official_approval_rate, 0)::numeric AS official_approval_pct,
        COALESCE(vcs.audited_citizen_votes, 0) AS audited_citizen_votes,
        COALESCE(vcs.web_votes_count, 0) AS web_votes_count,
        COALESCE(vcs.iot_totem_votes_count, 0) AS iot_totem_votes_count,
        b.updated_at AS updated_at
    FROM bills b
    JOIN legislative_houses lh ON lh.id = b.house_id
    LEFT JOIN politicians p ON p.id = b.author_id
    LEFT JOIN vote_channel_stats vcs ON vcs.bill_id = b.id
)
SELECT
    bill_id,
    bill_external_id,
    bill_number,
    bill_year,
    bill_title,
    theme,
    status,
    is_urgent_vote,
    house_id,
    house_slug,
    house_short_name,
    level,
    author_name,
    votes_favor,
    votes_against,
    total_citizen_votes,
    COALESCE(citizen_favor_pct, 0::numeric) AS citizen_favor_pct,
    official_approval_pct,
    ROUND(
        GREATEST(
            0::numeric,
            100.0::numeric - ABS(COALESCE(citizen_favor_pct, 0::numeric) - official_approval_pct)
        ),
        2
    ) AS convergence_index,
    CASE
        WHEN GREATEST(0::numeric, 100.0::numeric - ABS(COALESCE(citizen_favor_pct, 0::numeric) - official_approval_pct)) >= 80
            THEN 'Alta Convergência'
        WHEN GREATEST(0::numeric, 100.0::numeric - ABS(COALESCE(citizen_favor_pct, 0::numeric) - official_approval_pct)) >= 50
            THEN 'Convergência Moderada'
        ELSE 'Desalinhamento Crítico'
    END AS alignment_classification,
    audited_citizen_votes,
    web_votes_count,
    iot_totem_votes_count,
    ROUND(
        (
            iot_totem_votes_count::numeric
            / NULLIF(web_votes_count + iot_totem_votes_count, 0)::numeric
        ) * 100.0,
        2
    ) AS iot_share_pct,
    updated_at
FROM bill_base;


-- -----------------------------------------------------------------------------
-- 3. Executive KPI Summary per Legislative House
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold_house_kpis AS
WITH house_fragmentation AS (
    SELECT DISTINCT
        house_id,
        house_fragmentation_index,
        effective_number_of_parties
    FROM gold_party_seat_composition
)
SELECT
    lh.id AS house_id,
    lh.slug AS house_slug,
    lh.short_name AS house_short_name,
    lh.level AS level,
    lh.total_seats AS total_seats,
    lh.followers_count AS followers_count,
    COUNT(gb.bill_id) AS monitored_bills_count,
    COUNT(gb.bill_id) FILTER (WHERE gb.status = 'Aprovado') AS approved_bills_count,
    COALESCE(SUM(gb.total_citizen_votes), 0) AS total_citizen_votes,
    ROUND(COALESCE(AVG(gb.citizen_favor_pct), 0::numeric), 2) AS avg_citizen_favor_pct,
    ROUND(COALESCE(AVG(gb.official_approval_pct), 0::numeric), 2) AS avg_official_approval_pct,
    ROUND(COALESCE(AVG(gb.convergence_index), 0::numeric), 2) AS avg_convergence_index,
    COALESCE(hf.house_fragmentation_index, 0::numeric) AS party_fragmentation_index,
    COALESCE(hf.effective_number_of_parties, 0::numeric) AS effective_number_of_parties,
    COALESCE(SUM(gb.web_votes_count), 0) AS web_votes_count,
    COALESCE(SUM(gb.iot_totem_votes_count), 0) AS iot_totem_votes_count,
    ROUND(
        (
            COALESCE(SUM(gb.iot_totem_votes_count), 0)::numeric
            / NULLIF(
                COALESCE(SUM(gb.web_votes_count), 0) + COALESCE(SUM(gb.iot_totem_votes_count), 0),
                0
            )::numeric
        ) * 100.0,
        2
    ) AS iot_share_pct
FROM legislative_houses lh
LEFT JOIN gold_bill_convergence_metrics gb ON gb.house_id = lh.id
LEFT JOIN house_fragmentation hf ON hf.house_id = lh.id
GROUP BY
    lh.id,
    lh.slug,
    lh.short_name,
    lh.level,
    lh.total_seats,
    lh.followers_count,
    hf.house_fragmentation_index,
    hf.effective_number_of_parties;


-- -----------------------------------------------------------------------------
-- 4. Bronze Layer Ingestion & Deduplication Lineage Audit
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW gold_bronze_ingestion_audit AS
SELECT
    source,
    entity_type,
    COUNT(*) AS total_raw_events,
    COUNT(DISTINCT external_id) AS distinct_external_ids,
    COUNT(*) - COUNT(DISTINCT external_id) AS duplicate_events_detected,
    ROUND(AVG(OCTET_LENGTH(raw_payload::text))::numeric, 2) AS avg_payload_bytes,
    MIN(ingested_at) AS first_ingested_at,
    MAX(ingested_at) AS last_ingested_at
FROM raw_legislative_events
GROUP BY source, entity_type
ORDER BY last_ingested_at DESC;
