import React from 'react';
import { Bell, Settings } from 'lucide-react';
import { NavigationTab } from '../types/quorum';

interface NavbarProps {
  activeTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  followedCount: number;
  onOpenDrawer: () => void;
  userEmail: string | null;
  onOpenAccount: () => void;
}

const NAV_ITEMS: Array<{
  id: NavigationTab;
  label: string;
  shortLabel: string;
}> = [
  {
    id: 'feed',
    label: 'Na Pauta',
    shortLabel: 'Na Pauta',
  },
  {
    id: 'communities',
    label: 'Comunidades',
    shortLabel: 'Comunidades',
  },
  {
    id: 'profile',
    label: 'Parlamentares e Partidos',
    shortLabel: 'Parlamentares',
  },
  {
    id: 'dashboard',
    label: 'Panorama',
    shortLabel: 'Panorama',
  },
];

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onSelectTab,
  followedCount,
  onOpenDrawer,
  userEmail,
  onOpenAccount,
}) => {
  return (
    <header className="sticky top-0 z-30 border-b border-[#E2E8F0] bg-[#FFFFFF]">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        {/* Minimalist Editorial Brand */}
        <button
          type="button"
          onClick={() => onSelectTab('feed')}
          className="flex items-baseline gap-2.5 py-3.5 text-left transition-opacity hover:opacity-80"
        >
          <span className="inline-flex items-center gap-1.5 text-lg font-bold tracking-tight text-[#0F172A]">
            <span className="h-2 w-2 rounded-full bg-[#009C3B]" aria-hidden="true" />
            Quorum
          </span>
          <span className="hidden text-xs font-medium text-slate-500 sm:inline">
            Transparência Legislativa
          </span>
        </button>

        {/* Inline Editorial Navigation Tabs */}
        <nav
          aria-label="Navegação principal"
          className="order-3 flex w-full items-center gap-6 overflow-x-auto border-t border-[#E2E8F0] lg:order-2 lg:w-auto lg:border-t-0"
        >
          {NAV_ITEMS.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelectTab(item.id)}
                className={`relative shrink-0 border-b-2 py-3.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'border-[#002776] font-semibold text-[#002776]'
                    : 'border-transparent text-slate-500 hover:text-[#0F172A]'
                }`}
              >
                <span className="hidden sm:inline">{item.label}</span>
                <span className="sm:hidden">{item.shortLabel}</span>
              </button>
            );
          })}
        </nav>

        {/* Right Actions: Followed Houses & Account */}
        <div className="order-2 flex items-center gap-2 lg:order-3">
          <button
            type="button"
            onClick={onOpenDrawer}
            className="inline-flex items-center gap-2 rounded-lg border border-[#E2E8F0] bg-white px-3 py-1.5 text-xs font-semibold text-[#0F172A] transition-colors hover:border-slate-300 hover:bg-[#F8FAFC]"
            aria-label="Abrir preferências de casas legislativas seguidas"
          >
            <Bell className="h-3.5 w-3.5 text-slate-500" />
            <span className="hidden sm:inline">Casas Seguidas</span>
            <span className="tabular-nums inline-flex h-5 min-w-[20px] items-center justify-center rounded-md bg-[#009C3B]/10 px-1.5 text-xs font-bold text-[#009C3B]">
              {followedCount}
            </span>
          </button>

          {userEmail ? (
            <button
              type="button"
              onClick={onOpenAccount}
              className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors ${
                activeTab === 'account'
                  ? 'border-[#002776] bg-[#002776]/5 text-[#002776]'
                  : 'border-[#E2E8F0] bg-white text-[#0F172A] hover:border-slate-300 hover:bg-[#F8FAFC]'
              }`}
              title={userEmail}
            >
              <Settings className="h-3.5 w-3.5" />
              <span>Minha Conta</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={onOpenAccount}
              className="inline-flex items-center rounded-lg bg-[#002776] px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-[#1D4ED8]"
            >
              Entrar / Criar Conta
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
