import React from 'react';
import { Bell, BellOff, Check, X } from 'lucide-react';
import { LegislativeHouse } from '../types/quorum';

interface FollowedDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  houses: LegislativeHouse[];
  followedHouseIds: string[];
  voteAlertsEnabled: boolean;
  onToggleFollow: (houseId: string) => void;
  onToggleVoteAlerts: () => void;
  onOpenCommunity: (houseId: string) => void;
}

export const FollowedDrawer: React.FC<FollowedDrawerProps> = ({
  isOpen,
  onClose,
  houses,
  followedHouseIds,
  voteAlertsEnabled,
  onToggleFollow,
  onToggleVoteAlerts,
  onOpenCommunity,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/30 backdrop-blur-[1px]"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Editorial Drawer Panel */}
      <aside
        aria-label="Configurações de Casas Seguidas"
        className="animate-slide-in-right relative z-10 flex h-full w-full max-w-md flex-col border-l border-[#E2E8F0] bg-[#FFFFFF]"
      >
        <div className="flex items-center justify-between border-b border-[#E2E8F0] bg-white px-5 py-4">
          <div>
            <h2 className="text-base font-bold text-[#0F172A]">Casas Seguidas</h2>
            <p className="text-xs text-slate-500">
              Preferências locais de acompanhamento legislativo
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-[#F8FAFC] hover:text-[#0F172A]"
            aria-label="Fechar painel"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto p-5">
          {/* Voting Priority Preference */}
          <div className="flex items-start justify-between gap-4 border-b border-[#E2E8F0] pb-5">
            <div className="flex items-start gap-2.5">
              {voteAlertsEnabled ? (
                <Bell className="mt-0.5 h-4 w-4 shrink-0 text-[#002776]" />
              ) : (
                <BellOff className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
              )}
              <div>
                <h3 className="text-sm font-semibold text-[#0F172A]">
                  Priorizar votações próximas
                </h3>
                <p className="mt-0.5 text-xs leading-relaxed text-slate-500">
                  Ordena no início do feed os projetos com votação agendada para hoje ou amanhã.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={onToggleVoteAlerts}
              className={`shrink-0 rounded-md px-3 py-1 text-xs font-semibold transition-colors ${
                voteAlertsEnabled
                  ? 'bg-[#009C3B] text-white'
                  : 'border border-[#E2E8F0] bg-white text-slate-600'
              }`}
            >
              {voteAlertsEnabled ? 'Ativo' : 'Pausado'}
            </button>
          </div>

          {/* Simplified Legislative House Rows */}
          <div>
            <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Comunidades Legislativas ({followedHouseIds.length} seguidas)
            </h3>

            <div className="divide-y divide-[#E2E8F0] rounded-lg border border-[#E2E8F0]">
              {houses.map((house) => {
                const isFollowed = followedHouseIds.includes(house.id);
                return (
                  <div
                    key={house.id}
                    className="flex items-center justify-between gap-3 bg-white px-4 py-3"
                  >
                    <div className="min-w-0">
                      <button
                        type="button"
                        onClick={() => {
                          onOpenCommunity(house.id);
                          onClose();
                        }}
                        className="truncate text-left text-sm font-semibold text-[#0F172A] hover:text-[#002776] hover:underline"
                      >
                        {house.shortName}
                      </button>
                      <p className="text-xs text-slate-500">
                        {house.sphere} · {house.stateOrCity}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => onToggleFollow(house.id)}
                      className={`inline-flex shrink-0 items-center gap-1 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                        isFollowed
                          ? 'bg-[#009C3B]/10 text-[#009C3B] hover:bg-[#009C3B]/20'
                          : 'border border-[#E2E8F0] bg-white text-[#0F172A] hover:border-slate-300 hover:bg-[#F8FAFC]'
                      }`}
                    >
                      {isFollowed && <Check className="h-3.5 w-3.5" />}
                      <span>{isFollowed ? 'Seguindo' : 'Seguir'}</span>
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          <p className="text-xs leading-relaxed text-slate-500">
            Suas escolhas de acompanhamento são armazenadas apenas localmente nesta sessão, sem criação de perfil público.
          </p>
        </div>
      </aside>
    </div>
  );
};
