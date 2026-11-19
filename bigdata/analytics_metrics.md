# Funções Analíticas e Métricas de Negócio — Quorum

Este documento especifica as **4 funções analíticas principais** da camada **Gold** da plataforma **Quorum** (Área 2 — Big Data e Visualização, item `04: Funções analíticas / DAX e SQL`), traduzindo dados legislativos e participação cívica em indicadores objetivos para tomada de decisão.

---

## 1. Percentual de Apoio Cidadão (`Citizen_Favor_Pct`)

Mede a proporção de votos `"A Favor"` em relação ao total de votos válidos registrados nas enquetes do portal Web e dos Totens IoT para cada proposição.

- **Fórmula Matemática:**
  $$\text{Citizen\_Favor\_Pct} = \frac{\text{votes\_favor}}{\text{votes\_favor} + \text{votes\_against}} \times 100$$
- **Regra de Decisão:** Permite comparar rapidamente a aceitação popular de projetos complexos (após leitura em Desjuridiquês) por Casa Legislativa e status de tramitação.

### Implementação PostgreSQL 16 (SQL)
```sql
ROUND(
    (
        b.votes_favor::numeric
        / NULLIF(b.votes_favor + b.votes_against, 0)::numeric
    ) * 100.0,
    2
) AS citizen_favor_pct
```

### Fórmula Power BI (DAX)
```dax
Citizen Favor % =
VAR FavorVotes = SUM(gold_bill_convergence_metrics[votes_favor])
VAR TotalVotes =
    SUM(gold_bill_convergence_metrics[votes_favor])
    + SUM(gold_bill_convergence_metrics[votes_against])
RETURN
    ROUND(DIVIDE(FavorVotes, TotalVotes, 0) * 100, 2)
```

---

## 2. Índice de Convergência Cidadão-Parlamento (`Convergence_Index`)

Mede o grau de alinhamento (de `0` a `100`) entre a vontade expressa pelos cidadãos na plataforma e a taxa de adesão/aprovação oficial dentro das Casas Legislativas. Quanto mais próximo de **100%**, maior a sintonia entre eleitores e representantes.

- **Fórmula Matemática:**
  $$\text{Convergence\_Index} = \max\left(0,\; 100 - \left|\text{Citizen\_Favor\_Pct} - \text{Official\_Approval\_Pct}\right|\right)$$
- **Faixas de Classificação (Decisão Executiva):**
  - `>= 80%`: **Alta Convergência** (forte alinhamento cívico-parlamentar)
  - `50% – 79,9%`: **Convergência Moderada** (requer atenção em audiência pública)
  - `< 50%`: **Desalinhamento Crítico** (alerta prioritário de gap representativo)

### Implementação PostgreSQL 16 (SQL)
```sql
ROUND(
    GREATEST(
        0::numeric,
        100.0::numeric - ABS(citizen_favor_pct - COALESCE(official_approval_rate, 0)::numeric)
    ),
    2
) AS convergence_index
```

### Fórmula Power BI (DAX)
```dax
Convergence Index =
VAR AvgCitizenPct = [Citizen Favor %]
VAR AvgOfficialPct = AVERAGE(gold_bill_convergence_metrics[official_approval_pct])
VAR RawConvergence = 100 - ABS(AvgCitizenPct - AvgOfficialPct)
RETURN
    ROUND(MAX(0, RawConvergence), 2)

Convergence Band =
VAR Score = [Convergence Index]
RETURN
    SWITCH(
        TRUE(),
        Score >= 80, "Alta Convergência",
        Score >= 50, "Convergência Moderada",
        "Desalinhamento Crítico"
    )
```

---

## 3. Índice de Fragmentação Partidária — HHI Normalizado (`Party_Fragmentation_HHI`)

Baseado no índice de **Herfindahl-Hirschman (HHI)** invertido (índice de diversidade de Gini-Simpson), quantifica o grau de dispersão do poder entre os partidos dentro de uma Casa Legislativa. Complementarmente, calcula-se o **Número Efetivo de Partidos (ENP / Laakso-Taagepera)**.

- **Fórmula Matemática:**
  $$s_i = \frac{\text{seat\_count}_i}{\text{total\_seats}}, \qquad \text{HHI\_Bruto} = \sum_{i=1}^{n} s_i^2$$
  $$\text{Party\_Fragmentation\_HHI} = \left(1 - \sum_{i=1}^{n} s_i^2\right) \times 100, \qquad \text{ENP} = \frac{1}{\sum_{i=1}^{n} s_i^2}$$
- **Regra de Decisão:** Valores próximos a **90%+** (como na Câmara dos Deputados) indicam necessidade de coalizões amplas para aprovação de projetos; valores menores indicam maior concentração em poucos blocos partidários.

### Implementação PostgreSQL 16 (SQL)
```sql
ROUND(
    (
        1.0::numeric - SUM(
            POWER(seat_count::numeric / NULLIF(total_seats, 0)::numeric, 2)
        )
    ) * 100.0,
    2
) AS party_fragmentation_index,
ROUND(
    1.0::numeric / NULLIF(
        SUM(POWER(seat_count::numeric / NULLIF(total_seats, 0)::numeric, 2)),
        0
    ),
    2
) AS effective_number_of_parties
```

### Fórmula Power BI (DAX)
```dax
Party Fragmentation HHI % =
VAR HouseTotalSeats = MAX(gold_party_seat_composition[total_seats])
VAR SumSquaredShares =
    SUMX(
        gold_party_seat_composition,
        POWER(
            DIVIDE(gold_party_seat_composition[seat_count], HouseTotalSeats, 0),
            2
        )
    )
RETURN
    ROUND((1 - SumSquaredShares) * 100, 2)

Effective Parties ENP =
VAR HouseTotalSeats = MAX(gold_party_seat_composition[total_seats])
VAR SumSquaredShares =
    SUMX(
        gold_party_seat_composition,
        POWER(
            DIVIDE(gold_party_seat_composition[seat_count], HouseTotalSeats, 0),
            2
        )
    )
RETURN
    ROUND(DIVIDE(1, SumSquaredShares, 0), 2)
```

---

## 4. Taxa de Participação Omnichannel — Web vs. Totem IoT (`Omnichannel_Participation_Rate`)

Mede a distribuição dos votos auditados em `citizen_votes` por canal de entrada (`web` vs. `iot_totem`), permitindo avaliar a eficácia dos totens físicos em estações, terminais e equipamentos públicos na inclusão digital de cidadãos sem acesso contínuo à internet.

- **Fórmula Matemática:**
  $$\text{IoT\_Share\_Pct} = \frac{\text{votes}_{\text{iot\_totem}}}{\text{votes}_{\text{web}} + \text{votes}_{\text{iot\_totem}}} \times 100$$
- **Regra de Decisão:** Orienta a alocação física de novos totens IoT em municípios ou bairros onde o engajamento digital via Web ainda é baixo.

### Implementação PostgreSQL 16 (SQL)
```sql
COUNT(cv.id) FILTER (WHERE cv.source = 'web') AS web_votes_count,
COUNT(cv.id) FILTER (WHERE cv.source = 'iot_totem') AS iot_totem_votes_count,
ROUND(
    (
        COUNT(cv.id) FILTER (WHERE cv.source = 'iot_totem')::numeric
        / NULLIF(COUNT(cv.id) FILTER (WHERE cv.source IN ('web', 'iot_totem')), 0)::numeric
    ) * 100.0,
    2
) AS iot_share_pct
```

### Fórmula Power BI (DAX)
```dax
Web Votes =
CALCULATE(
    SUM(gold_bill_convergence_metrics[web_votes_count])
)

IoT Totem Votes =
CALCULATE(
    SUM(gold_bill_convergence_metrics[iot_totem_votes_count])
)

IoT Participation Share % =
VAR IoT = [IoT Totem Votes]
VAR TotalAuditVotes = [Web Votes] + IoT
RETURN
    ROUND(DIVIDE(IoT, TotalAuditVotes, 0) * 100, 2)
```
