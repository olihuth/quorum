import React, { useMemo, useState } from 'react';
import { Search, Sparkles } from 'lucide-react';
import { BillCard } from '../components/BillCard';
import { TranslatePreviewModal } from '../components/TranslatePreviewModal';
import { Bill, BillStatus, LegislativeHouse, VoteOption } from '../types/quorum';

interface FeedPageProps {
  bills: Bill[];
  houses: LegislativeHouse[];
  followedHouseIds: string[];
  voteAlertsEnabled: boolean;
  userVotes: Record<string, VoteOption>;
  likedBillIds: string[];
  onVote: (billId: string, option: VoteOption) => void;
  onToggleLike: (billId: string) => void;
  onShare: (bill: Bill) => void;
  onSelectHouse: (houseId: string) => void;
  onSelectPolitician: (politicianId: string) => void;
  onSelectParty: (partyAcronym: string) => void;
}

type CommunityFilter = 'all' | 'followed' | string;
type StatusFilter = 'all' | BillStatus;

export const FeedPage: React.FC<FeedPageProps> = ({
  bills,
  houses,
  followedHouseIds,
  voteAlertsEnabled,
  userVotes,
  likedBillIds,
  onVote,
  onToggleLike,
  onShare,
  onSelectHouse,
  onSelectPolitician,
  onSelectParty,
}) => {
  const [communityFilter, setCommunityFilter] = useState<CommunityFilter>('followed');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isTranslateModalOpen, setIsTranslateModalOpen] = useState(false);

  const filteredBills = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    return bills
      .filter((bill) => {
        if (communityFilter === 'followed') {
          if (!followedHouseIds.includes(bill.houseId)) return false;
        } else if (communityFilter !== 'all') {
          if (bill.houseId !== communityFilter) return false;
        }

        if (statusFilter !== 'all' && bill.status !== statusFilter) {
          return false;
        }

        if (query) {
          const matchesText =
            bill.number.toLowerCase().includes(query) ||
            bill.title.toLowerCase().includes(query) ||
            bill.theme.toLowerCase().includes(query) ||
            bill.authorName.toLowerCase().includes(query) ||
            bill.houseShortName.toLowerCase().includes(query);
          if (!matchesText) return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (voteAlertsEnabled) {
          if (a.isUrgentVote && !b.isUrgentVote) return -1;
          if (!a.isUrgentVote && b.isUrgentVote) return 1;
        }
        return 0;
      });
  }, [bills, communityFilter, followedHouseIds, searchQuery, statusFilter, voteAlertsEnabled]);

  const statusOptions: Array<{ value: StatusFilter; label: string }> = [
    { value: 'all', label: 'Todos' },
    { value: 'Votação Agendada', label: 'Votação Agendada' },
    { value: 'Em Tramitação', label: 'Em Tramitação' },
    { value: 'Aprovado', label: 'Aprovado' },
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      {/* Compact Editorial Filter Header */}
      <section aria-label="Filtros de projetos de lei" className="space-y-3 border-b border-[#E2E8F0] pb-4">
        {/* Row 1: Page Title + Compact Search */}
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div className="flex items-baseline gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">Na Pauta</h1>
            <span className="tabular-nums text-xs font-medium text-slate-400">
              {filteredBills.length}{' '}
              {filteredBills.length === 1 ? 'proposição' : 'proposições'}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="relative flex-1 sm:w-56 sm:flex-initial">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar PL, tema ou autor..."
                className="w-full rounded-lg border border-[#E2E8F0] bg-white py-1.5 pl-8 pr-3 text-xs text-[#0F172A] placeholder:text-slate-400 focus:border-[#002776] focus:outline-none"
              />
            </div>

            <button
              type="button"
              onClick={() => setIsTranslateModalOpen(true)}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-[#E2E8F0] bg-white px-3 py-1.5 text-xs font-semibold text-[#002776] transition-colors hover:border-[#002776] hover:bg-[#F8FAFC]"
            >
              <Sparkles className="h-3.5 w-3.5 text-[#EAB308]" />
              <span>Traduzir um PL (IA)</span>
            </button>
          </div>
        </div>

        {/* Row 2: Legislative House Pills + Status Selector */}
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              onClick={() => setCommunityFilter('followed')}
              className={`tabular-nums rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                communityFilter === 'followed'
                  ? 'bg-[#009C3B] text-white'
                  : 'bg-white text-[#009C3B] ring-1 ring-[#009C3B]/30 hover:bg-emerald-50'
              }`}
            >
              Seguidas ({followedHouseIds.length})
            </button>

            <button
              type="button"
              onClick={() => setCommunityFilter('all')}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                communityFilter === 'all'
                  ? 'bg-[#002776] text-white'
                  : 'bg-white text-slate-600 ring-1 ring-[#E2E8F0] hover:bg-slate-50'
              }`}
            >
              Todas
            </button>

            {houses.map((house) => (
              <button
                key={house.id}
                type="button"
                onClick={() => setCommunityFilter(house.id)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                  communityFilter === house.id
                    ? 'bg-[#1D4ED8] text-white'
                    : 'bg-white text-slate-600 ring-1 ring-[#E2E8F0] hover:bg-slate-50'
                }`}
              >
                {house.shortName}
              </button>
            ))}
          </div>

          <div className="shrink-0">
            <label htmlFor="feed-status-filter" className="sr-only">
              Filtrar por status
            </label>
            <select
              id="feed-status-filter"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="w-full rounded-md border border-[#E2E8F0] bg-white px-2.5 py-1 text-xs font-medium text-[#0F172A] focus:border-[#002776] focus:outline-none sm:w-auto"
            >
              {statusOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  Status: {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {/* Bills List */}
      {filteredBills.length === 0 ? (
        <div className="rounded-lg border border-dashed border-[#E2E8F0] bg-white p-10 text-center">
          <p className="text-sm font-semibold text-[#0F172A]">
            Nenhum projeto encontrado para os filtros atuais.
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Limpe a busca ou selecione outra Casa Legislativa.
          </p>
          <button
            type="button"
            onClick={() => {
              setCommunityFilter('all');
              setStatusFilter('all');
              setSearchQuery('');
            }}
            className="mt-4 rounded-md border border-[#E2E8F0] bg-white px-3.5 py-1.5 text-xs font-semibold text-[#002776] hover:bg-[#F8FAFC]"
          >
            Restaurar filtros
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredBills.map((bill) => (
            <BillCard
              key={bill.id}
              bill={bill}
              userVote={userVotes[bill.id]}
              isLiked={likedBillIds.includes(bill.id)}
              onVote={onVote}
              onToggleLike={onToggleLike}
              onShare={onShare}
              onSelectHouse={onSelectHouse}
              onSelectPolitician={onSelectPolitician}
              onSelectParty={onSelectParty}
            />
          ))}
        </div>
      )}

      <TranslatePreviewModal
        isOpen={isTranslateModalOpen}
        onClose={() => setIsTranslateModalOpen(false)}
      />
    </div>
  );
};
