import React, { useMemo, useState } from 'react';
import { Bill, LegislativeHouse, VoteOption } from '../types/quorum';

interface DashboardPageProps {
  houses: LegislativeHouse[];
  bills: Bill[];
  userVotes: Record<string, VoteOption>;
  onSelectHouse: (houseId: string) => void;
  onSelectParty: (partyAcronym: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  houses,
  bills,
  userVotes,
  onSelectHouse,
  onSelectParty,
}) => {
  const [selectedHouseId, setSelectedHouseId] = useState<string>(
    houses[0]?.id ?? 'congresso-nacional',
  );
  const [billHouseFilter, setBillHouseFilter] = useState<string>('all');

  const selectedHouse = useMemo(
    () => houses.find((h) => h.id === selectedHouseId) ?? houses[0],
    [houses, selectedHouseId],
  );

  const filteredBills = useMemo(() => {
    if (billHouseFilter === 'all') return bills;
    return bills.filter((b) => b.houseId === billHouseFilter);
  }, [billHouseFilter, bills]);

  const kpis = useMemo(() => {
    const totalBills = filteredBills.length;
    const totalCitizenVotes = filteredBills.reduce((acc, bill) => {
      const userChoice = userVotes[bill.id];
      return acc + bill.votesInFavor + bill.votesAgainst + (userChoice ? 1 : 0);
    }, 0);

    const approvedCount = filteredBills.filter((b) => b.status === 'Aprovado').length;
    const approvalRate = totalBills > 0 ? Math.round((approvedCount / totalBills) * 100) : 0;

    const avgCitizenFavor =
      totalBills > 0
        ? Math.round(
            filteredBills.reduce((acc, bill) => {
              const userChoice = userVotes[bill.id];
              const favor = bill.votesInFavor + (userChoice === 'favor' ? 1 : 0);
              const against = bill.votesAgainst + (userChoice === 'against' ? 1 : 0);
              const total = favor + against;
              return acc + (total > 0 ? (favor / total) * 100 : 0);
            }, 0) / totalBills,
          )
        : 0;

    return {
      totalBills,
      totalCitizenVotes,
      approvedCount,
      approvalRate,
      avgCitizenFavor,
    };
  }, [filteredBills, userVotes]);

  const donutSegments = useMemo(() => {
    if (!selectedHouse) return [];
    const radius = 58;
    const circumference = 2 * Math.PI * radius;
    let cumulativeFraction = 0;

    return selectedHouse.partyComposition.map((party) => {
      const fraction = party.seats / selectedHouse.totalSeats;
      const strokeLength = fraction * circumference;
      const dashOffset = -cumulativeFraction * circumference;
      cumulativeFraction += fraction;

      return {
        ...party,
        pct: Math.round(fraction * 100),
        strokeLength,
        dashOffset,
        circumference,
      };
    });
  }, [selectedHouse]);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header & House Filter */}
      <section className="flex flex-col justify-between gap-4 border-b border-[#E2E8F0] pb-4 lg:flex-row lg:items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">
            Panorama Legislativo
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Indicadores de participação cidadã, composição de bancadas e status oficial das proposições.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label
            htmlFor="bill-house-filter"
            className="text-xs font-medium text-slate-500"
          >
            Recorte:
          </label>
          <select
            id="bill-house-filter"
            value={billHouseFilter}
            onChange={(e) => {
              const value = e.target.value;
              setBillHouseFilter(value);
              if (value !== 'all') {
                setSelectedHouseId(value);
              }
            }}
            className="rounded-md border border-[#E2E8F0] bg-white px-3 py-1.5 text-xs font-semibold text-[#0F172A] focus:border-[#002776] focus:outline-none"
          >
            <option value="all">Todas as Casas Monitoradas</option>
            {houses.map((house) => (
              <option key={house.id} value={house.id}>
                {house.shortName} ({house.sphere})
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* Unified 4-Column Metric Strip */}
      <section
        aria-label="Indicadores legislativos"
        className="grid grid-cols-1 divide-y divide-[#E2E8F0] rounded-lg border border-[#E2E8F0] bg-white sm:grid-cols-2 sm:divide-x sm:divide-y-0 lg:grid-cols-4"
      >
        <div className="p-5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Projetos Monitorados
          </p>
          <p className="tabular-nums mt-2 text-3xl font-bold text-[#0F172A]">
            {kpis.totalBills}
          </p>
          <p className="mt-1 text-xs text-slate-500">Traduzidos por IA</p>
        </div>

        <div className="p-5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Participação Cidadã
          </p>
          <p className="tabular-nums mt-2 text-3xl font-bold text-[#009C3B]">
            {kpis.totalCitizenVotes.toLocaleString('pt-BR')}
          </p>
          <p className="mt-1 text-xs text-slate-500">Votos nas enquetes Quorum</p>
        </div>

        <div className="p-5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Taxa de Aprovação Oficial
          </p>
          <p className="tabular-nums mt-2 text-3xl font-bold text-[#002776]">
            {kpis.approvalRate}%
          </p>
          <p className="tabular-nums mt-1 text-xs text-slate-500">
            {kpis.approvedCount} de {kpis.totalBills} aprovados em plenário
          </p>
        </div>

        <div className="p-5">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Apoio Cidadão Médio
          </p>
          <p className="tabular-nums mt-2 text-3xl font-bold text-[#0F172A]">
            {kpis.avgCitizenFavor}%
          </p>
          <p className="mt-1 text-xs text-slate-500">Média de votos &ldquo;A Favor&rdquo;</p>
        </div>
      </section>

      {/* Main Flat Editorial Charts Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Party Seat Distribution Chart */}
        <section className="rounded-lg border border-[#E2E8F0] bg-white p-6 lg:col-span-5">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-4">
            <h2 className="text-sm font-bold text-[#0F172A]">
              Distribuição de Bancadas
            </h2>

            <select
              aria-label="Selecionar Casa Legislativa para gráfico de bancadas"
              value={selectedHouse.id}
              onChange={(e) => setSelectedHouseId(e.target.value)}
              className="rounded-md border border-[#E2E8F0] bg-white px-2.5 py-1 text-xs font-semibold text-[#0F172A] focus:border-[#002776] focus:outline-none"
            >
              {houses.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.shortName}
                </option>
              ))}
            </select>
          </div>

          <div className="mt-5 flex flex-col items-center gap-6 sm:flex-row lg:flex-col xl:flex-row">
            <div className="relative flex h-40 w-40 shrink-0 items-center justify-center">
              <svg viewBox="0 0 160 160" className="h-full w-full -rotate-90">
                <circle
                  cx="80"
                  cy="80"
                  r="58"
                  fill="none"
                  stroke="#E2E8F0"
                  strokeWidth="18"
                />
                {donutSegments.map((seg) => (
                  <circle
                    key={seg.partyAcronym}
                    cx="80"
                    cy="80"
                    r="58"
                    fill="none"
                    stroke={seg.color}
                    strokeWidth="18"
                    strokeDasharray={`${seg.strokeLength} ${seg.circumference}`}
                    strokeDashoffset={seg.dashOffset}
                  />
                ))}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="tabular-nums text-2xl font-bold text-[#0F172A]">
                  {selectedHouse.totalSeats}
                </span>
                <span className="text-[11px] font-medium text-slate-500">cadeiras</span>
              </div>
            </div>

            <div className="w-full space-y-2.5">
              {donutSegments.slice(0, 7).map((party) => {
                const canInspect = party.partyAcronym !== 'Outros';

                return (
                  <div key={party.partyAcronym} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <button
                        type="button"
                        disabled={!canInspect}
                        onClick={() => canInspect && onSelectParty(party.partyAcronym)}
                        className={`inline-flex items-center gap-1.5 font-semibold ${
                          canInspect
                            ? 'text-[#0F172A] hover:text-[#1D4ED8] hover:underline'
                            : 'cursor-default text-slate-500'
                        }`}
                      >
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: party.color }}
                        />
                        {party.partyAcronym}
                      </button>
                      <span className="tabular-nums text-slate-500">
                        {party.seats} ({party.pct}%)
                      </span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${Math.max(party.pct, 3)}%`,
                          backgroundColor: party.color,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-5 flex items-center justify-between border-t border-[#E2E8F0] pt-3 text-xs">
            <span className="text-slate-500">{selectedHouse.shortName}</span>
            <button
              type="button"
              onClick={() => onSelectHouse(selectedHouse.id)}
              className="font-semibold text-[#002776] hover:underline"
            >
              Ver painel da Casa →
            </button>
          </div>
        </section>

        {/* Citizen Poll vs Official Legislative Status Comparison */}
        <section className="rounded-lg border border-[#E2E8F0] bg-white p-6 lg:col-span-7">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-4">
            <h2 className="text-sm font-bold text-[#0F172A]">
              Enquete Cidadã Quorum vs. Apoio Oficial
            </h2>

            <div className="flex items-center gap-4 text-xs font-medium text-slate-600">
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-[#009C3B]" />
                Cidadãos (A Favor)
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-[#1D4ED8]" />
                Adesão Oficial
              </span>
            </div>
          </div>

          <div className="divide-y divide-[#E2E8F0]">
            {filteredBills.map((bill) => {
              const userChoice = userVotes[bill.id];
              const favor = bill.votesInFavor + (userChoice === 'favor' ? 1 : 0);
              const against = bill.votesAgainst + (userChoice === 'against' ? 1 : 0);
              const total = favor + against;
              const citizenPct = total > 0 ? Math.round((favor / total) * 100) : 0;
              const officialPct = bill.officialApprovalRate ?? 70;

              return (
                <div key={bill.id} className="py-4 first:pt-4 last:pb-0">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-[#002776]">
                        {bill.number}
                      </span>
                      <span className="text-slate-300">·</span>
                      <span className="text-slate-500">{bill.houseShortName}</span>
                    </div>

                    <span
                      className={`font-semibold ${
                        bill.status === 'Aprovado'
                          ? 'text-[#009C3B]'
                          : bill.status === 'Votação Agendada'
                            ? 'text-amber-700'
                            : 'text-[#1D4ED8]'
                      }`}
                    >
                      {bill.status}
                    </span>
                  </div>

                  <p className="mt-1 text-xs font-semibold text-[#0F172A]">{bill.title}</p>

                  <div className="mt-2.5 grid grid-cols-1 gap-2 sm:grid-cols-2 sm:gap-4">
                    <div>
                      <div className="tabular-nums mb-1 flex justify-between text-[11px] font-medium">
                        <span className="text-[#009C3B]">Cidadãos</span>
                        <span className="text-slate-600">
                          {citizenPct}% ({total.toLocaleString('pt-BR')})
                        </span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-[#009C3B] transition-all duration-300"
                          style={{ width: `${citizenPct}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="tabular-nums mb-1 flex justify-between text-[11px] font-medium">
                        <span className="text-[#1D4ED8]">Aprovação Oficial</span>
                        <span className="text-slate-600">{officialPct}%</span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-[#1D4ED8]"
                          style={{ width: `${officialPct}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
};
