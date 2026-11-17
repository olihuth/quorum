import React, { useMemo } from 'react';
import { Check, ExternalLink, X } from 'lucide-react';
import {
  Bill,
  LegislativeHouse,
  PartyInfo,
  Politician,
  ProfileViewTarget,
} from '../types/quorum';

interface PoliticianProfilePageProps {
  target: ProfileViewTarget;
  politicians: Politician[];
  parties: PartyInfo[];
  bills: Bill[];
  houses: LegislativeHouse[];
  onSelectTarget: (target: ProfileViewTarget) => void;
  onSelectHouse: (houseId: string) => void;
  onOpenBillInFeed: () => void;
}

export const PoliticianProfilePage: React.FC<PoliticianProfilePageProps> = ({
  target,
  politicians,
  parties,
  bills,
  houses,
  onSelectTarget,
  onSelectHouse,
  onOpenBillInFeed,
}) => {
  const activePolitician = useMemo(() => {
    if (target.type === 'politician') {
      return politicians.find((p) => p.id === target.id) ?? politicians[0];
    }
    return null;
  }, [politicians, target]);

  const activeParty = useMemo(() => {
    if (target.type === 'party') {
      return parties.find((p) => p.acronym === target.acronym) ?? parties[0];
    }
    return null;
  }, [parties, target]);

  const authoredBills = useMemo(() => {
    if (!activePolitician) return [];
    return bills.filter((b) => activePolitician.authoredBillIds.includes(b.id));
  }, [activePolitician, bills]);

  const partyPoliticians = useMemo(() => {
    if (!activeParty) return [];
    return politicians.filter((p) => p.partyAcronym === activeParty.acronym);
  }, [activeParty, politicians]);

  const partyHouseSeats = useMemo(() => {
    if (!activeParty) return [];
    return houses
      .map((house) => {
        const seatEntry = house.partyComposition.find(
          (item) => item.partyAcronym === activeParty.acronym,
        );
        return {
          houseId: house.id,
          houseShortName: house.shortName,
          sphere: house.sphere,
          seats: seatEntry?.seats ?? 0,
          totalSeats: house.totalSeats,
        };
      })
      .filter((entry) => entry.seats > 0);
  }, [activeParty, houses]);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Clean Editorial Selector Header */}
      <section className="space-y-4 border-b border-[#E2E8F0] pb-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">
              Parlamentares e Partidos
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Ficha institucional somente leitura · Sem botões de seguir, curtidas ou feed social.
            </p>
          </div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Registro Público Oficial
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div>
            <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Parlamentares
            </p>
            <div className="flex flex-wrap gap-1.5">
              {politicians.map((pol) => {
                const isSelected =
                  target.type === 'politician' && target.id === pol.id;
                return (
                  <button
                    key={pol.id}
                    type="button"
                    onClick={() => onSelectTarget({ type: 'politician', id: pol.id })}
                    className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                      isSelected
                        ? 'bg-[#002776] text-white'
                        : 'bg-white text-slate-700 ring-1 ring-[#E2E8F0] hover:bg-slate-50'
                    }`}
                  >
                    {pol.name} ({pol.partyAcronym})
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Partidos
            </p>
            <div className="flex flex-wrap gap-1.5">
              {parties.map((party) => {
                const isSelected =
                  target.type === 'party' && target.acronym === party.acronym;
                return (
                  <button
                    key={party.acronym}
                    type="button"
                    onClick={() =>
                      onSelectTarget({ type: 'party', acronym: party.acronym })
                    }
                    className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                      isSelected
                        ? 'bg-[#1D4ED8] text-white'
                        : 'bg-white text-slate-700 ring-1 ring-[#E2E8F0] hover:bg-slate-50'
                    }`}
                  >
                    {party.acronym}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Politician Read-Only Sheet */}
      {activePolitician && (
        <>
          <section className="rounded-lg border border-[#E2E8F0] bg-white p-6">
            <div className="flex flex-col justify-between gap-5 md:flex-row md:items-start">
              <div>
                <p className="text-xs font-semibold text-slate-500">
                  <span className="text-[#002776]">{activePolitician.role}</span>
                  <span className="mx-1.5 text-slate-300">·</span>
                  <button
                    type="button"
                    onClick={() =>
                      onSelectTarget({
                        type: 'party',
                        acronym: activePolitician.partyAcronym,
                      })
                    }
                    className="text-[#1D4ED8] hover:underline"
                  >
                    {activePolitician.partyAcronym} — {activePolitician.partyName}
                  </button>
                </p>

                <h2 className="mt-2 text-2xl font-bold tracking-tight text-[#0F172A]">
                  {activePolitician.name}
                </h2>

                <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <span>{activePolitician.stateOrCity}</span>
                  <span className="text-slate-300">·</span>
                  <button
                    type="button"
                    onClick={() => onSelectHouse(activePolitician.houseId)}
                    className="font-semibold text-[#002776] hover:underline"
                  >
                    {activePolitician.houseShortName}
                  </button>
                  <span className="text-slate-300">·</span>
                  <span>{activePolitician.legislature}</span>
                </div>

                <p className="mt-3 max-w-2xl text-sm leading-relaxed text-slate-600">
                  {activePolitician.biographySummary}
                </p>
              </div>

              <div className="flex shrink-0 flex-col gap-2 md:items-end">
                <a
                  href={activePolitician.officialPortalUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-md border border-[#E2E8F0] bg-white px-3.5 py-2 text-xs font-semibold text-[#002776] transition-colors hover:border-[#002776]"
                >
                  <span>Ficha no Portal Oficial</span>
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
                <p className="tabular-nums text-xs text-slate-500">
                  Presença oficial:{' '}
                  <strong className="text-[#009C3B]">
                    {activePolitician.attendanceRate}
                  </strong>
                </p>
              </div>
            </div>
          </section>

          {/* Authored Bills */}
          <section className="rounded-lg border border-[#E2E8F0] bg-white p-6">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <h3 className="text-sm font-bold text-[#0F172A]">
                Projetos de Lei de Autoria ({authoredBills.length})
              </h3>
              <button
                type="button"
                onClick={onOpenBillInFeed}
                className="text-xs font-semibold text-[#1D4ED8] hover:underline"
              >
                Votar na enquete no feed →
              </button>
            </div>

            <div className="divide-y divide-[#E2E8F0]">
              {authoredBills.map((bill) => (
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
                  <h4 className="mt-1.5 text-sm font-bold text-[#0F172A]">{bill.title}</h4>
                  <p className="mt-1 text-xs leading-relaxed text-slate-600">
                    {bill.aiSummaryBullets[0]}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* Official Voting History Table */}
          <section className="rounded-lg border border-[#E2E8F0] bg-white p-6">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#E2E8F0] pb-3">
              <h3 className="text-sm font-bold text-[#0F172A]">
                Histórico Oficial de Votações
              </h3>
              <span className="text-xs text-slate-400">
                Voto nominal vs. enquete cidadã Quorum
              </span>
            </div>

            <div className="mt-3 overflow-x-auto">
              <table className="w-full min-w-[600px] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-[#E2E8F0] text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                    <th className="py-2.5 pr-4">Proposição</th>
                    <th className="py-2.5 pr-4">Casa / Data</th>
                    <th className="py-2.5 pr-4">Voto Oficial</th>
                    <th className="py-2.5">Maioria Cidadã</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0]">
                  {activePolitician.votingHistory.map((record) => {
                    const votedYes = record.officialVote === 'Sim';
                    const votedNo = record.officialVote === 'Não';
                    return (
                      <tr key={`${record.billId}-${record.date}`}>
                        <td className="py-3 pr-4">
                          <span className="font-mono text-xs font-semibold text-[#1D4ED8]">
                            {record.billNumber}
                          </span>
                          <p className="mt-0.5 text-xs font-medium text-[#0F172A]">
                            {record.billTitle}
                          </p>
                        </td>
                        <td className="py-3 pr-4 text-xs text-slate-500">
                          <p className="font-medium text-[#0F172A]">
                            {record.houseShortName}
                          </p>
                          <p>{record.date}</p>
                        </td>
                        <td className="py-3 pr-4 text-xs">
                          {votedYes ? (
                            <span className="inline-flex items-center gap-1 font-semibold text-[#009C3B]">
                              <Check className="h-3.5 w-3.5" />
                              Votou Sim
                            </span>
                          ) : votedNo ? (
                            <span className="inline-flex items-center gap-1 font-semibold text-red-700">
                              <X className="h-3.5 w-3.5" />
                              Votou Não
                            </span>
                          ) : (
                            <span className="font-medium text-slate-500">Abstenção</span>
                          )}
                        </td>
                        <td className="py-3 text-xs font-medium text-slate-700">
                          {record.citizenMajorityVote}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {/* Party Read-Only Sheet */}
      {activeParty && (
        <>
          <section className="rounded-lg border border-[#E2E8F0] bg-white p-6">
            <div className="flex flex-col justify-between gap-5 md:flex-row md:items-start">
              <div>
                <p className="text-xs font-semibold text-slate-500">
                  <span className="font-mono text-[#002776]">
                    TSE nº {activeParty.registrationNumber}
                  </span>
                  <span className="mx-1.5 text-slate-300">·</span>
                  <span>Espectro: {activeParty.spectrum}</span>
                  <span className="mx-1.5 text-slate-300">·</span>
                  <span>Fundado em {activeParty.foundationYear}</span>
                </p>

                <div className="mt-2 flex items-center gap-2.5">
                  <span
                    className="h-3 w-3 shrink-0 rounded-full"
                    style={{ backgroundColor: activeParty.color }}
                    aria-hidden="true"
                  />
                  <h2 className="text-2xl font-bold tracking-tight text-[#0F172A]">
                    {activeParty.name} ({activeParty.acronym})
                  </h2>
                </div>

                <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
                  {activeParty.programSummary}
                </p>
              </div>

              <a
                href={activeParty.officialPortalUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-[#E2E8F0] bg-white px-3.5 py-2 text-xs font-semibold text-[#002776] transition-colors hover:border-[#002776]"
              >
                <span>Registro Oficial no TSE</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          </section>

          {/* Party Seats Across Legislative Houses */}
          <section className="rounded-lg border border-[#E2E8F0] bg-white p-6">
            <h3 className="border-b border-[#E2E8F0] pb-3 text-sm font-bold text-[#0F172A]">
              Representação nas Casas Legislativas Monitoradas
            </h3>

            <div className="mt-4 grid grid-cols-1 divide-y divide-[#E2E8F0] rounded-lg border border-[#E2E8F0] sm:grid-cols-2 sm:divide-x sm:divide-y-0 lg:grid-cols-4">
              {partyHouseSeats.map((item) => {
                const pct = Math.round((item.seats / item.totalSeats) * 100);
                return (
                  <button
                    key={item.houseId}
                    type="button"
                    onClick={() => onSelectHouse(item.houseId)}
                    className="p-4 text-left transition-colors hover:bg-[#F8FAFC]"
                  >
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                      {item.sphere}
                    </p>
                    <p className="mt-1 text-sm font-bold text-[#0F172A]">
                      {item.houseShortName}
                    </p>
                    <p className="tabular-nums mt-2 text-xl font-bold text-[#002776]">
                      {item.seats}{' '}
                      <span className="text-xs font-normal text-slate-500">
                        / {item.totalSeats} ({pct}%)
                      </span>
                    </p>
                  </button>
                );
              })}
            </div>
          </section>

          {/* Affiliated Monitored Representatives */}
          <section className="rounded-lg border border-[#E2E8F0] bg-white p-6">
            <h3 className="border-b border-[#E2E8F0] pb-3 text-sm font-bold text-[#0F172A]">
              Parlamentares desta Bancada com Pautas em Destaque
            </h3>

            {partyPoliticians.length === 0 ? (
              <p className="mt-4 text-sm text-slate-500">
                Nenhum parlamentar individual desta legenda com proposição ativa nesta amostra mockada.
              </p>
            ) : (
              <div className="divide-y divide-[#E2E8F0]">
                {partyPoliticians.map((pol) => (
                  <button
                    key={pol.id}
                    type="button"
                    onClick={() => onSelectTarget({ type: 'politician', id: pol.id })}
                    className="flex w-full items-center justify-between py-3.5 text-left transition-colors hover:bg-[#F8FAFC]"
                  >
                    <div>
                      <p className="text-sm font-semibold text-[#0F172A]">{pol.name}</p>
                      <p className="text-xs text-slate-500">
                        {pol.role} · {pol.houseShortName} · {pol.stateOrCity}
                      </p>
                    </div>
                    <span className="text-xs font-semibold text-[#1D4ED8]">
                      Ver ficha →
                    </span>
                  </button>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
};
