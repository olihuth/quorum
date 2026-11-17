import React, { useState } from 'react';
import { Check, Heart, Share2, ThumbsDown, ThumbsUp } from 'lucide-react';
import { Bill, VoteOption } from '../types/quorum';

interface BillCardProps {
  bill: Bill;
  userVote?: VoteOption;
  isLiked: boolean;
  onVote: (billId: string, option: VoteOption) => void;
  onToggleLike: (billId: string) => void;
  onShare: (bill: Bill) => void;
  onSelectHouse: (houseId: string) => void;
  onSelectPolitician: (politicianId: string) => void;
  onSelectParty: (partyAcronym: string) => void;
}

export const BillCard: React.FC<BillCardProps> = ({
  bill,
  userVote,
  isLiked,
  onVote,
  onToggleLike,
  onShare,
  onSelectHouse,
  onSelectPolitician,
  onSelectParty,
}) => {
  const [showFormalText, setShowFormalText] = useState(false);

  const totalVotesInFavor = bill.votesInFavor + (userVote === 'favor' ? 1 : 0);
  const totalVotesAgainst = bill.votesAgainst + (userVote === 'against' ? 1 : 0);
  const totalPollVotes = totalVotesInFavor + totalVotesAgainst;

  const favorPercent =
    totalPollVotes > 0 ? Math.round((totalVotesInFavor / totalPollVotes) * 100) : 50;
  const againstPercent = 100 - favorPercent;

  const displayLikes = bill.likesCount + (isLiked ? 1 : 0);

  const renderStatusIndicator = () => {
    if (bill.status === 'Aprovado') {
      return (
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#009C3B]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#009C3B]" aria-hidden="true" />
          Aprovado
        </span>
      );
    }

    if (bill.status === 'Votação Agendada') {
      return (
        <span className="inline-flex items-center gap-1.5 rounded bg-[#FFDF00]/25 px-2 py-0.5 text-xs font-semibold text-amber-800">
          <span className="h-1.5 w-1.5 rounded-full bg-[#EAB308]" aria-hidden="true" />
          Votação: {bill.nextVoteDate}
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-[#1D4ED8]">
        <span className="h-1.5 w-1.5 rounded-full bg-[#1D4ED8]" aria-hidden="true" />
        Em Tramitação · {bill.nextVoteDate}
      </span>
    );
  };

  return (
    <article className="rounded-lg border border-[#E2E8F0] bg-[#FFFFFF] p-5 sm:p-6">
      {/* Header Metadata Line (Only 3 items: House, Bill Number, Status/Schedule) */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onSelectHouse(bill.houseId)}
            className="text-xs font-semibold text-[#002776] hover:underline"
          >
            {bill.houseShortName}
          </button>
          <span className="text-slate-300" aria-hidden="true">
            ·
          </span>
          <span className="font-mono text-xs font-medium text-slate-500">
            {bill.number}
          </span>
        </div>

        <div>{renderStatusIndicator()}</div>
      </div>

      {/* Title & Author Byline */}
      <div className="mt-3">
        <h3 className="text-lg font-bold leading-snug tracking-tight text-[#0F172A] sm:text-xl">
          {bill.title}
        </h3>

        <p className="mt-1.5 text-xs text-slate-500">
          Por{' '}
          <button
            type="button"
            onClick={() => onSelectPolitician(bill.authorId)}
            className="font-medium text-slate-700 hover:text-[#002776] hover:underline"
          >
            {bill.authorName}
          </button>{' '}
          <button
            type="button"
            onClick={() => onSelectParty(bill.authorParty)}
            className="font-medium text-slate-500 hover:text-[#1D4ED8] hover:underline"
          >
            ({bill.authorParty}-{bill.authorState})
          </button>
        </p>
      </div>

      {/* Clean Editorial Desjuridiquês List */}
      <div className="my-4 border-l-2 border-[#EAB308] pl-4">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Desjuridiquês · Resumo por IA
        </p>

        <ul className="mt-2 space-y-1.5 text-sm leading-relaxed text-slate-700">
          {bill.aiSummaryBullets.map((bullet, index) => (
            <li key={index} className="flex items-start gap-2.5">
              <span
                className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#009C3B]"
                aria-hidden="true"
              />
              <span>{bullet}</span>
            </li>
          ))}
        </ul>

        <button
          type="button"
          onClick={() => setShowFormalText((prev) => !prev)}
          className="mt-2.5 text-xs font-medium text-slate-400 transition-colors hover:text-[#002776]"
        >
          {showFormalText ? 'Ocultar ementa oficial' : 'Ver ementa oficial'}
        </button>

        {showFormalText && (
          <p className="mt-2 text-xs leading-relaxed text-slate-500">
            {bill.formalSummary}
          </p>
        )}
      </div>

      {/* Compact Voting & Action Bar */}
      <div className="mt-4 flex flex-col gap-3 border-t border-[#E2E8F0] pt-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Citizen Vote Controls + Sleek Split Progress Bar */}
        <div className="flex flex-1 flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              disabled={Boolean(userVote)}
              onClick={() => onVote(bill.id, 'favor')}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                userVote === 'favor'
                  ? 'bg-[#009C3B] text-white'
                  : userVote
                    ? 'cursor-not-allowed border border-[#E2E8F0] bg-white text-slate-400'
                    : 'bg-[#009C3B] text-white hover:bg-[#16A34A]'
              }`}
            >
              {userVote === 'favor' ? (
                <Check className="h-3.5 w-3.5" />
              ) : (
                <ThumbsUp className="h-3.5 w-3.5" />
              )}
              <span>A Favor</span>
            </button>

            <button
              type="button"
              disabled={Boolean(userVote)}
              onClick={() => onVote(bill.id, 'against')}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                userVote === 'against'
                  ? 'bg-[#0F172A] text-white'
                  : userVote
                    ? 'cursor-not-allowed border border-[#E2E8F0] bg-white text-slate-400'
                    : 'border border-[#E2E8F0] bg-white text-slate-700 hover:border-slate-300 hover:bg-[#F8FAFC]'
              }`}
            >
              {userVote === 'against' ? (
                <Check className="h-3.5 w-3.5" />
              ) : (
                <ThumbsDown className="h-3.5 w-3.5" />
              )}
              <span>Contra</span>
            </button>

            <div className="tabular-nums flex items-center gap-2 text-xs text-slate-500 sm:ml-1">
              <span className="font-semibold text-[#009C3B]">{favorPercent}%</span>
              <span>/</span>
              <span>{againstPercent}%</span>
              <span className="text-slate-400">
                ({totalPollVotes.toLocaleString('pt-BR')} votos)
              </span>
            </div>
          </div>

          <div className="flex h-1.5 w-full max-w-md overflow-hidden rounded-full bg-slate-200">
            <div
              className="bg-[#009C3B] transition-all duration-300"
              style={{ width: `${favorPercent}%` }}
            />
          </div>
        </div>

        {/* Minimal Like & Share Actions */}
        <div className="flex items-center gap-2 self-start sm:self-center">
          <button
            type="button"
            onClick={() => onToggleLike(bill.id)}
            className={`tabular-nums inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs font-medium transition-colors ${
              isLiked
                ? 'border-[#009C3B]/40 bg-[#009C3B]/10 text-[#009C3B]'
                : 'border-[#E2E8F0] bg-white text-slate-600 hover:bg-[#F8FAFC]'
            }`}
            aria-label="Apoiar projeto"
          >
            <Heart className={`h-3.5 w-3.5 ${isLiked ? 'fill-[#009C3B] text-[#009C3B]' : ''}`} />
            <span>Apoiar</span>
            <span className="font-semibold">{displayLikes.toLocaleString('pt-BR')}</span>
          </button>

          <button
            type="button"
            onClick={() => onShare(bill)}
            className="inline-flex items-center gap-1.5 rounded-md border border-[#E2E8F0] bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-slate-300 hover:bg-[#F8FAFC] hover:text-[#0F172A]"
            aria-label="Compartilhar projeto"
          >
            <Share2 className="h-3.5 w-3.5" />
            <span>Compartilhar</span>
          </button>
        </div>
      </div>
    </article>
  );
};
