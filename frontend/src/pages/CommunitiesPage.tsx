import React, { useMemo, useState } from 'react';
import { ArrowLeft, Check, ExternalLink, Plus } from 'lucide-react';
import { BillCard } from '../components/BillCard';
import {
  Bill,
  LegislativeHouse,
  Politician,
  VoteOption,
} from '../types/quorum';

interface CommunitiesPageProps {
  houses: LegislativeHouse[];
  bills: Bill[];
  politicians: Politician[];
  followedHouseIds: string[];
  selectedHouseId: string | null;
  userVotes: Record<string, VoteOption>;
  likedBillIds: string[];
  onSelectHouse: (houseId: string | null) => void;
  onToggleFollow: (houseId: string) => void;
  onVote: (billId: string, option: VoteOption) => void;
  onToggleLike: (billId: string) => void;
  onShare: (bill: Bill) => void;
  onSelectPolitician: (politicianId: string) => void;
  onSelectParty: (partyAcronym: string) => void;
}

type CommunityBillTab = 'all' | 'active' | 'approved';

export const CommunitiesPage: React.FC<CommunitiesPageProps> = ({
  houses,
  bills,
  politicians,
  followedHouseIds,
  selectedHouseId,
  userVotes,
  likedBillIds,
  onSelectHouse,
  onToggleFollow,
  onVote,
  onToggleLike,
  onShare,
  onSelectPolitician,
  onSelectParty,
}) => {
  const [billTab, setBillTab] = useState<CommunityBillTab>('all');

  const selectedHouse = useMemo(
    () => houses.find((h) => h.id === selectedHouseId) ?? null,
    [houses, selectedHouseId],
  );

  const houseBills = useMemo(() => {
    if (!selectedHouse) return [];
    return bills
      .filter((b) => b.houseId === selectedHouse.id)
      .filter((b) => {
        if (billTab === 'approved') return b.status === 'Aprovado';
        if (billTab === 'active') return b.status !== 'Aprovado';
        return true;
      });
  }, [billTab, bills, selectedHouse]);

  const housePoliticians = useMemo(() => {
    if (!selectedHouse) return [];
    return politicians.filter((p) => p.houseId === selectedHouse.id);
  }, [politicians, selectedHouse]);

  // Dedicated Community Detail View
  if (selectedHouse) {
    const isFollowed = followedHouseIds.includes(selectedHouse.id);
    const totalBillsCount = bills.filter((b) => b.houseId === selectedHouse.id).length;

    return (
      <div className="mx-auto max-w-5xl space-y-6">
        {/* Top Breadcrumb */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => {
              setBillTab('all');
              onSelectHouse(null);
            }}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 transition-colors hover:text-[#002776]"
          >
            <ArrowLeft className="h-4 w-4" />
            Todas as Comunidades Legislativas
          </button>

          <a
            href={selectedHouse.officialPortalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs font-semibold text-[#1D4ED8] hover:underline"
          >
            <span>Portal oficial da Casa</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>

        {/* Clean Institutional Header Sheet */}
        <section className="rounded-lg border border-[#E2E8F0] bg-white p-6">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
            <div className="max-w-2xl">
              <p className="text-xs font-semibold text-slate-500">
                <span className="text-[#002776]">Esfera {selectedHouse.sphere}</span>
                <span className="mx-2 text-slate-300">·</span>
                <span>{selectedHouse.stateOrCity}</span>
                <span className="mx-2 text-slate-300">·</span>
                <span className="tabular-nums">{selectedHouse.totalSeats} cadeiras</span>
              </p>

              <h1 className="mt-2 text-2xl font-bold tracking-tight text-[#0F172A]">
                {selectedHouse.name}
              </h1>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                {selectedHouse.description}
              </p>
            </div>

            <div className="flex shrink-0 flex-col items-start gap-1.5 md:items-end">
              <button
                type="button"
                onClick={() => onToggleFollow(selectedHouse.id)}
                className={`inline-flex items-center gap-1.5 rounded-md px-4 py-2 text-xs font-semibold transition-colors ${
                  isFollowed
                    ? 'bg-[#009C3B] text-white hover:bg-[#16A34A]'
                    : 'bg-[#002776] text-white hover:bg-[#1D4ED8]'
                }`}
              >
                {isFollowed ? <Check className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
                <span>{isFollowed ? 'Seguindo' : 'Seguir Casa'}</span>
              </button>
              <span className="tabular-nums text-xs text-slate-500">
                {(selectedHouse.followersCount + (isFollowed ? 1 : 0)).toLocaleString('pt-BR')}{' '}
                seguidores
              </span>
            </div>
          </div>
        </section>

        {/* Agenda + Party Composition */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Upcoming Sessions */}
          <section className="rounded-lg border border-[#E2E8F0] bg-white p-5">
            <h2 className="border-b border-[#E2E8F0] pb-3 text-sm font-bold text-[#0F172A]">
              Agenda de Sessões e Votações
            </h2>

            <div className="divide-y divide-[#E2E8F0]">
              {selectedHouse.upcomingSessions.map((session) => (
                <div key={session.id} className="py-3.5 first:pt-4 last:pb-0">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <span className="rounded bg-[#FFDF00]/25 px-2 py-0.5 font-semibold text-amber-900">
                      {session.date} · {session.time}
                    </span>
                    <span className="font-medium text-slate-500">{session.type}</span>
                  </div>
                  <p className="mt-1.5 text-sm font-semibold text-[#0F172A]">
                    {session.title}
                  </p>
                  <p className="mt-1 font-mono text-xs text-[#1D4ED8]">
                    Em pauta: {session.highlightedBills.join(', ')}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* Party Seat Composition */}
          <section className="rounded-lg border border-[#E2E8F0] bg-white p-5">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <h2 className="text-sm font-bold text-[#0F172A]">
                Composição de Bancadas ({selectedHouse.totalSeats} cadeiras)
              </h2>
              <span className="text-xs text-slate-400">Clique no partido</span>
            </div>

            <div className="mt-4 flex h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
              {selectedHouse.partyComposition.map((party) => {
                const widthPct = (party.seats / selectedHouse.totalSeats) * 100;
                return (
                  <div
                    key={party.partyAcronym}
                    title={`${party.partyAcronym}: ${party.seats} cadeiras`}
                    style={{
                      width: `${widthPct}%`,
                      backgroundColor: party.color,
                    }}
                  />
                );
              })}
            </div>

            <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3">
              {selectedHouse.partyComposition.map((party) => {
                const pct = Math.round((party.seats / selectedHouse.totalSeats) * 100);
                const isClickable =
                  party.partyAcronym !== 'Outros' &&
                  party.partyAcronym !== 'PP' &&
                  party.partyAcronym !== 'REPUBLICANOS';

                return (
                  <button
                    key={party.partyAcronym}
                    type="button"
                    disabled={!isClickable}
                    onClick={() => isClickable && onSelectParty(party.partyAcronym)}
                    className={`flex items-center justify-between border-b border-[#E2E8F0] py-1.5 text-left text-xs transition-colors ${
                      isClickable
                        ? 'hover:text-[#1D4ED8]'
                        : 'cursor-default text-slate-500'
                    }`}
                  >
                    <span className="inline-flex items-center gap-1.5 font-semibold text-[#0F172A]">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: party.color }}
                      />
                      {party.partyAcronym}
                    </span>
                    <span className="tabular-nums text-slate-500">
                      {party.seats} ({pct}%)
                    </span>
                  </button>
                );
              })}
            </div>
          </section>
        </div>

        {/* Monitored Representatives in this House */}
        <section className="rounded-lg border border-[#E2E8F0] bg-white p-5">
          <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
            <h2 className="text-sm font-bold text-[#0F172A]">
              Parlamentares Monitorados na Casa
            </h2>
            <span className="text-xs text-slate-400">Perfis informativos</span>
          </div>

          <div className="mt-3 divide-y divide-[#E2E8F0]">
            {housePoliticians.map((pol) => (
              <button
                key={pol.id}
                type="button"
                onClick={() => onSelectPolitician(pol.id)}
                className="flex w-full items-center justify-between gap-4 py-3 text-left transition-colors hover:bg-[#F8FAFC]"
              >
                <div>
                  <p className="text-sm font-semibold text-[#0F172A]">{pol.name}</p>
                  <p className="text-xs text-slate-500">
                    {pol.role} · {pol.partyAcronym} · {pol.stateOrCity}
                  </p>
                </div>
                <span className="text-xs font-semibold text-[#1D4ED8]">
                  Ver histórico →
                </span>
              </button>
            ))}
          </div>
        </section>

        {/* Filterable Bills List */}
        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E2E8F0] pb-3">
            <h2 className="text-base font-bold text-[#0F172A]">
              Projetos de Lei ({totalBillsCount})
            </h2>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setBillTab('all')}
                className={`rounded-md px-3 py-1 text-xs font-semibold transition-colors ${
                  billTab === 'all'
                    ? 'bg-[#002776] text-white'
                    : 'bg-white text-slate-600 ring-1 ring-[#E2E8F0] hover:bg-slate-50'
                }`}
              >
                Todos
              </button>
              <button
                type="button"
                onClick={() => setBillTab('active')}
                className={`rounded-md px-3 py-1 text-xs font-semibold transition-colors ${
                  billTab === 'active'
                    ? 'bg-[#1D4ED8] text-white'
                    : 'bg-white text-slate-600 ring-1 ring-[#E2E8F0] hover:bg-slate-50'
                }`}
              >
                Em Tramitação / Pauta
              </button>
              <button
                type="button"
                onClick={() => setBillTab('approved')}
                className={`rounded-md px-3 py-1 text-xs font-semibold transition-colors ${
                  billTab === 'approved'
                    ? 'bg-[#009C3B] text-white'
                    : 'bg-white text-slate-600 ring-1 ring-[#E2E8F0] hover:bg-slate-50'
                }`}
              >
                Aprovados
              </button>
            </div>
          </div>

          {houseBills.length === 0 ? (
            <div className="rounded-lg border border-dashed border-[#E2E8F0] bg-white p-8 text-center text-sm text-slate-500">
              Nenhum projeto nesta categoria para {selectedHouse.shortName}.
            </div>
          ) : (
            <div className="space-y-4">
              {houseBills.map((bill) => (
                <BillCard
                  key={bill.id}
                  bill={bill}
                  userVote={userVotes[bill.id]}
                  isLiked={likedBillIds.includes(bill.id)}
                  onVote={onVote}
                  onToggleLike={onToggleLike}
                  onShare={onShare}
                  onSelectHouse={(id) => onSelectHouse(id)}
                  onSelectPolitician={onSelectPolitician}
                  onSelectParty={onSelectParty}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    );
  }

  // Directory Grid View (4 Legislative Houses)
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <section className="flex flex-col justify-between gap-2 border-b border-[#E2E8F0] pb-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">
            Comunidades Legislativas
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Acompanhe casas legislativas para filtrar proposições, consultar agendas e verificar bancadas.
          </p>
        </div>
        <span className="tabular-nums text-xs font-semibold text-[#009C3B]">
          {followedHouseIds.length} de {houses.length} acompanhadas
        </span>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {houses.map((house) => {
          const isFollowed = followedHouseIds.includes(house.id);
          const houseBillsCount = bills.filter((b) => b.houseId === house.id).length;
          const nextSession = house.upcomingSessions[0];

          return (
            <article
              key={house.id}
              className="flex flex-col justify-between rounded-lg border border-[#E2E8F0] bg-white p-5 sm:p-6"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <p className="text-xs font-semibold text-slate-500">
                    <span className="text-[#002776]">{house.sphere}</span>
                    <span className="mx-1.5 text-slate-300">·</span>
                    <span>{house.stateOrCity}</span>
                  </p>

                  <button
                    type="button"
                    onClick={() => onToggleFollow(house.id)}
                    className={`inline-flex shrink-0 items-center gap-1 rounded-md px-3 py-1 text-xs font-semibold transition-colors ${
                      isFollowed
                        ? 'bg-[#009C3B]/10 text-[#009C3B] hover:bg-[#009C3B]/20'
                        : 'border border-[#E2E8F0] bg-white text-[#0F172A] hover:border-[#002776] hover:text-[#002776]'
                    }`}
                  >
                    {isFollowed ? (
                      <Check className="h-3.5 w-3.5" />
                    ) : (
                      <Plus className="h-3.5 w-3.5" />
                    )}
                    <span>{isFollowed ? 'Seguindo' : 'Seguir'}</span>
                  </button>
                </div>

                <h2 className="mt-2.5 text-lg font-bold leading-snug text-[#0F172A]">
                  {house.name}
                </h2>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-600">
                  {house.description}
                </p>

                <div className="tabular-nums mt-4 flex flex-wrap items-center gap-4 text-xs text-slate-500">
                  <span>
                    <strong className="text-[#0F172A]">{house.totalSeats}</strong> cadeiras
                  </span>
                  <span>
                    <strong className="text-[#1D4ED8]">{houseBillsCount}</strong> PLs em pauta
                  </span>
                  <span>
                    <strong className="text-[#009C3B]">
                      {(house.followersCount + (isFollowed ? 1 : 0)).toLocaleString('pt-BR')}
                    </strong>{' '}
                    seguidores
                  </span>
                </div>

                {nextSession && (
                  <p className="mt-3 border-l-2 border-[#EAB308] pl-3 text-xs text-slate-600">
                    <span className="font-semibold text-[#0F172A]">
                      Próxima agenda ({nextSession.date}, {nextSession.time}):
                    </span>{' '}
                    {nextSession.title}
                  </p>
                )}
              </div>

              <div className="mt-5 flex items-center justify-between border-t border-[#E2E8F0] pt-3.5">
                <button
                  type="button"
                  onClick={() => onSelectHouse(house.id)}
                  className="text-xs font-semibold text-[#002776] hover:underline"
                >
                  Abrir painel da Casa →
                </button>
                <a
                  href={house.officialPortalUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-[#0F172A]"
                >
                  <span>Site oficial</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
};
