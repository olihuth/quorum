import React, { useState } from 'react';
import { Check, Lock, LogOut, Mail, Plus } from 'lucide-react';
import {
  LegislativeHouse,
  UserAccount,
  UserNotificationSettings,
} from '../types/quorum';

interface AccountSettingsPageProps {
  account: UserAccount;
  houses: LegislativeHouse[];
  followedHouseIds: string[];
  onUpdateEmail: (newEmail: string) => string | null;
  onUpdatePassword: (currentPassword: string, newPassword: string) => string | null;
  onUpdateNotifications: (next: UserNotificationSettings) => void;
  onToggleFollow: (houseId: string) => void;
  onLogout: () => void;
}

export const AccountSettingsPage: React.FC<AccountSettingsPageProps> = ({
  account,
  houses,
  followedHouseIds,
  onUpdateEmail,
  onUpdatePassword,
  onUpdateNotifications,
  onToggleFollow,
  onLogout,
}) => {
  const [newEmail, setNewEmail] = useState(account.email);
  const [emailError, setEmailError] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const handleEmailSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setEmailError(null);

    const normalized = newEmail.trim().toLowerCase();
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(normalized)) {
      setEmailError('Informe um endereço de e-mail válido.');
      return;
    }

    const err = onUpdateEmail(normalized);
    if (err) {
      setEmailError(err);
    }
  };

  const handlePasswordSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setPasswordError(null);

    if (newPassword.length < 6) {
      setPasswordError('A nova senha deve ter pelo menos 6 caracteres.');
      return;
    }

    if (newPassword !== confirmNewPassword) {
      setPasswordError('A confirmação da nova senha não confere.');
      return;
    }

    const err = onUpdatePassword(currentPassword, newPassword);
    if (err) {
      setPasswordError(err);
      return;
    }

    setCurrentPassword('');
    setNewPassword('');
    setConfirmNewPassword('');
  };

  const notificationOptions: Array<{
    key: keyof UserNotificationSettings;
    title: string;
    description: string;
  }> = [
    {
      key: 'urgentVoteAlerts',
      title: 'Priorizar votações próximas no topo do feed',
      description:
        'Ordena automaticamente proposições com votação agendada para hoje ou amanhã.',
    },
    {
      key: 'emailDigest',
      title: 'Resumo semanal por e-mail das Casas Seguidas',
      description:
        'Receba um boletim consolidado com os projetos aprovados e pautas da semana.',
    },
    {
      key: 'statusChangeNotifications',
      title: 'Alertas de tramitação e resultado oficial de plenário',
      description:
        'Notifica quando um projeto em que você votou avança de comissão ou é votado.',
    },
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <section className="flex flex-col justify-between gap-3 border-b border-[#E2E8F0] pb-4 sm:flex-row sm:items-center">
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#009C3B]">
            Área Privada · Sem Perfil Público
          </span>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-[#0F172A]">
            Configurações da Conta (Privado)
          </h1>
          <p className="mt-1 text-xs text-slate-500">
            Gerencie seu acesso, notificações e Casas Legislativas acompanhadas. Estes dados não são visíveis a outros usuários.
          </p>
        </div>

        <button
          type="button"
          onClick={onLogout}
          className="inline-flex shrink-0 items-center gap-1.5 self-start rounded-md border border-[#E2E8F0] bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition-colors hover:border-red-300 hover:bg-red-50 hover:text-red-700 sm:self-center"
        >
          <LogOut className="h-3.5 w-3.5" />
          <span>Sair da conta</span>
        </button>
      </section>

      {/* Email Settings */}
      <section className="rounded-lg border border-[#E2E8F0] bg-white p-6">
        <div className="border-b border-[#E2E8F0] pb-3">
          <h2 className="text-sm font-bold text-[#0F172A]">
            Dados de Acesso · Alterar E-mail
          </h2>
          <p className="mt-0.5 text-xs text-slate-500">
            E-mail atual: <strong className="text-[#0F172A]">{account.email}</strong>
          </p>
        </div>

        <form onSubmit={handleEmailSubmit} className="mt-4 space-y-3" noValidate>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex-1">
              <label
                htmlFor="settings-email"
                className="block text-xs font-semibold text-[#0F172A]"
              >
                Novo e-mail
              </label>
              <div className="relative mt-1.5">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  id="settings-email"
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full rounded-md border border-[#E2E8F0] bg-white py-2 pl-9 pr-3 text-sm text-[#0F172A] focus:border-[#002776] focus:outline-none"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="rounded-md bg-[#002776] px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-[#1D4ED8]"
            >
              Salvar e-mail
            </button>
          </div>

          {emailError && (
            <p className="text-xs font-medium text-red-700" role="alert">
              {emailError}
            </p>
          )}
        </form>
      </section>

      {/* Password Settings */}
      <section className="rounded-lg border border-[#E2E8F0] bg-white p-6">
        <div className="border-b border-[#E2E8F0] pb-3">
          <h2 className="text-sm font-bold text-[#0F172A]">
            Segurança · Alterar Senha
          </h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Utilize uma senha com no mínimo 6 caracteres.
          </p>
        </div>

        <form onSubmit={handlePasswordSubmit} className="mt-4 space-y-4" noValidate>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label
                htmlFor="settings-current-password"
                className="block text-xs font-semibold text-[#0F172A]"
              >
                Senha atual
              </label>
              <div className="relative mt-1.5">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                <input
                  id="settings-current-password"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full rounded-md border border-[#E2E8F0] bg-white py-2 pl-8 pr-3 text-sm text-[#0F172A] focus:border-[#002776] focus:outline-none"
                  required
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="settings-new-password"
                className="block text-xs font-semibold text-[#0F172A]"
              >
                Nova senha
              </label>
              <div className="relative mt-1.5">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                <input
                  id="settings-new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full rounded-md border border-[#E2E8F0] bg-white py-2 pl-8 pr-3 text-sm text-[#0F172A] focus:border-[#002776] focus:outline-none"
                  required
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="settings-confirm-password"
                className="block text-xs font-semibold text-[#0F172A]"
              >
                Confirmar nova senha
              </label>
              <div className="relative mt-1.5">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                <input
                  id="settings-confirm-password"
                  type="password"
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  className="w-full rounded-md border border-[#E2E8F0] bg-white py-2 pl-8 pr-3 text-sm text-[#0F172A] focus:border-[#002776] focus:outline-none"
                  required
                />
              </div>
            </div>
          </div>

          {passwordError && (
            <p className="text-xs font-medium text-red-700" role="alert">
              {passwordError}
            </p>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              className="rounded-md bg-[#002776] px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-[#1D4ED8]"
            >
              Atualizar senha
            </button>
          </div>
        </form>
      </section>

      {/* Notification Preferences */}
      <section className="rounded-lg border border-[#E2E8F0] bg-white p-6">
        <div className="border-b border-[#E2E8F0] pb-3">
          <h2 className="text-sm font-bold text-[#0F172A]">
            Preferências de Notificação
          </h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Escolha como deseja acompanhar a pauta legislativa.
          </p>
        </div>

        <div className="divide-y divide-[#E2E8F0]">
          {notificationOptions.map((item) => {
            const enabled = account.notifications[item.key];
            return (
              <div
                key={item.key}
                className="flex items-start justify-between gap-4 py-4 first:pt-4 last:pb-0"
              >
                <div>
                  <p className="text-sm font-semibold text-[#0F172A]">{item.title}</p>
                  <p className="mt-0.5 text-xs text-slate-500">{item.description}</p>
                </div>

                <button
                  type="button"
                  onClick={() =>
                    onUpdateNotifications({
                      ...account.notifications,
                      [item.key]: !enabled,
                    })
                  }
                  className={`shrink-0 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                    enabled
                      ? 'bg-[#009C3B] text-white'
                      : 'border border-[#E2E8F0] bg-white text-slate-600 hover:bg-[#F8FAFC]'
                  }`}
                >
                  {enabled ? 'Ativado' : 'Desativado'}
                </button>
              </div>
            );
          })}
        </div>
      </section>

      {/* Followed Legislative Houses */}
      <section className="rounded-lg border border-[#E2E8F0] bg-white p-6">
        <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
          <div>
            <h2 className="text-sm font-bold text-[#0F172A]">
              Casas Legislativas Seguidas
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              Por padrão, o feed exibe Congresso Nacional e Senado Federal; as demais casas são opcionais.
            </p>
          </div>
          <span className="tabular-nums text-xs font-semibold text-[#009C3B]">
            {followedHouseIds.length} seguidas
          </span>
        </div>

        <div className="divide-y divide-[#E2E8F0]">
          {houses.map((house) => {
            const isFollowed = followedHouseIds.includes(house.id);
            return (
              <div
                key={house.id}
                className="flex items-center justify-between gap-3 py-3 first:pt-4 last:pb-0"
              >
                <div>
                  <p className="text-sm font-semibold text-[#0F172A]">
                    {house.shortName}
                  </p>
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
            );
          })}
        </div>
      </section>
    </div>
  );
};
