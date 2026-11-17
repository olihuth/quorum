import React, { useCallback, useState } from 'react';
import { FollowedDrawer } from './components/FollowedDrawer';
import { Navbar } from './components/Navbar';
import { ToastContainer } from './components/Toast';
import {
  LEGISLATIVE_HOUSES,
  MOCK_BILLS,
  MOCK_PARTIES,
  MOCK_POLITICIANS,
} from './data/mockData';
import { AccountSettingsPage } from './pages/AccountSettingsPage';
import { AuthPage } from './pages/AuthPage';
import { CommunitiesPage } from './pages/CommunitiesPage';
import { DashboardPage } from './pages/DashboardPage';
import { FeedPage } from './pages/FeedPage';
import { PoliticianProfilePage } from './pages/PoliticianProfilePage';
import {
  Bill,
  NavigationTab,
  ProfileViewTarget,
  ToastNotification,
  UserAccount,
  UserNotificationSettings,
  VoteOption,
} from './types/quorum';

const DEFAULT_NOTIFICATIONS: UserNotificationSettings = {
  urgentVoteAlerts: true,
  emailDigest: true,
  statusChangeNotifications: false,
};

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('auth');
  const [selectedHouseId, setSelectedHouseId] = useState<string | null>(null);
  const [profileTarget, setProfileTarget] = useState<ProfileViewTarget>({
    type: 'politician',
    id: MOCK_POLITICIANS[0].id,
  });

  // Private Citizen Account State (no public citizen profile)
  const [registeredAccounts, setRegisteredAccounts] = useState<UserAccount[]>([]);
  const [currentUser, setCurrentUser] = useState<UserAccount | null>(null);

  // Followed Legislative Houses state (Congresso Nacional & Senado Federal by default)
  const [followedHouseIds, setFollowedHouseIds] = useState<string[]>(() =>
    LEGISLATIVE_HOUSES.filter((h) => h.isFollowedByDefault).map((h) => h.id),
  );
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [voteAlertsEnabled, setVoteAlertsEnabled] = useState(true);

  // Local state lock of 1 vote per bill & simple support counter toggle
  const [userVotes, setUserVotes] = useState<Record<string, VoteOption>>({});
  const [likedBillIds, setLikedBillIds] = useState<string[]>([]);

  // Portuguese Toast Notifications
  const [toasts, setToasts] = useState<ToastNotification[]>([]);

  const pushToast = useCallback(
    (message: string, variant: ToastNotification['variant'] = 'success') => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      setToasts((prev) => [...prev, { id, message, variant }]);
      window.setTimeout(() => {
        setToasts((prev) => prev.filter((item) => item.id !== id));
      }, 4000);
    },
    [],
  );

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const handleLogin = useCallback(
    (email: string, password: string): string | null => {
      const found = registeredAccounts.find((acc) => acc.email === email);
      if (!found) {
        return 'Conta não encontrada para este e-mail. Crie uma conta na aba "Criar Conta".';
      }
      if (found.passwordHash !== password) {
        return 'Senha incorreta. Tente novamente.';
      }
      setCurrentUser(found);
      setVoteAlertsEnabled(found.notifications.urgentVoteAlerts);
      setActiveTab('feed');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      pushToast(`Bem-vindo(a) de volta ao Quorum (${found.email})!`, 'success');
      return null;
    },
    [pushToast, registeredAccounts],
  );

  const handleRegister = useCallback(
    (email: string, password: string): string | null => {
      const exists = registeredAccounts.some((acc) => acc.email === email);
      if (exists) {
        return 'Já existe uma conta cadastrada com este e-mail.';
      }
      const newAccount: UserAccount = {
        email,
        passwordHash: password,
        createdAt: new Date().toISOString(),
        notifications: { ...DEFAULT_NOTIFICATIONS },
      };
      setRegisteredAccounts((prev) => [...prev, newAccount]);
      setCurrentUser(newAccount);
      setVoteAlertsEnabled(newAccount.notifications.urgentVoteAlerts);
      setActiveTab('feed');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      pushToast('Conta privada criada com sucesso! Exibindo suas Casas Seguidas.', 'success');
      return null;
    },
    [pushToast, registeredAccounts],
  );

  const handleLogout = useCallback(() => {
    setCurrentUser(null);
    setActiveTab('auth');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    pushToast('Você saiu da sua conta privada.', 'info');
  }, [pushToast]);

  const handleUpdateEmail = useCallback(
    (newEmail: string): string | null => {
      if (!currentUser) return 'Sessão expirada.';
      if (newEmail === currentUser.email) {
        return 'Informe um e-mail diferente do atual.';
      }
      const alreadyInUse = registeredAccounts.some(
        (acc) => acc.email === newEmail && acc.email !== currentUser.email,
      );
      if (alreadyInUse) {
        return 'Este e-mail já está vinculado a outra conta.';
      }

      const previousEmail = currentUser.email;
      const updatedUser: UserAccount = { ...currentUser, email: newEmail };
      setCurrentUser(updatedUser);
      setRegisteredAccounts((prev) =>
        prev.map((acc) => (acc.email === previousEmail ? updatedUser : acc)),
      );
      pushToast('E-mail atualizado com sucesso!', 'success');
      return null;
    },
    [currentUser, pushToast, registeredAccounts],
  );

  const handleUpdatePassword = useCallback(
    (currentPassword: string, newPassword: string): string | null => {
      if (!currentUser) return 'Sessão expirada.';
      if (currentUser.passwordHash !== currentPassword) {
        return 'A senha atual informada está incorreta.';
      }
      const updatedUser: UserAccount = { ...currentUser, passwordHash: newPassword };
      setCurrentUser(updatedUser);
      setRegisteredAccounts((prev) =>
        prev.map((acc) => (acc.email === currentUser.email ? updatedUser : acc)),
      );
      pushToast('Senha atualizada com sucesso!', 'success');
      return null;
    },
    [currentUser, pushToast],
  );

  const handleUpdateNotifications = useCallback(
    (nextNotifications: UserNotificationSettings) => {
      if (!currentUser) return;
      const updatedUser: UserAccount = {
        ...currentUser,
        notifications: nextNotifications,
      };
      setCurrentUser(updatedUser);
      setRegisteredAccounts((prev) =>
        prev.map((acc) => (acc.email === currentUser.email ? updatedUser : acc)),
      );
      setVoteAlertsEnabled(nextNotifications.urgentVoteAlerts);
      pushToast('Preferências de notificação atualizadas.', 'info');
    },
    [currentUser, pushToast],
  );

  const handleToggleFollow = useCallback(
    (houseId: string) => {
      const house = LEGISLATIVE_HOUSES.find((h) => h.id === houseId);
      setFollowedHouseIds((prev) => {
        const alreadyFollowing = prev.includes(houseId);
        if (alreadyFollowing) {
          pushToast(
            `Você deixou de seguir ${house?.shortName ?? 'esta Casa Legislativa'}.`,
            'info',
          );
          return prev.filter((id) => id !== houseId);
        }
        pushToast(
          `Agora você acompanha ${house?.shortName ?? 'esta Casa Legislativa'}!`,
          'success',
        );
        return [...prev, houseId];
      });
    },
    [pushToast],
  );

  const handleVote = useCallback(
    (billId: string, option: VoteOption) => {
      setUserVotes((prev) => {
        if (prev[billId]) return prev;
        const label = option === 'favor' ? 'A Favor' : 'Contra';
        pushToast(
          `Voto "${label}" registrado com sucesso na enquete cidadã!`,
          'success',
        );
        return { ...prev, [billId]: option };
      });
    },
    [pushToast],
  );

  const handleToggleLike = useCallback((billId: string) => {
    setLikedBillIds((prev) =>
      prev.includes(billId)
        ? prev.filter((id) => id !== billId)
        : [...prev, billId],
    );
  }, []);

  const handleShare = useCallback(
    async (bill: Bill) => {
      const mockUrl = `https://quorum.org.br/proposicoes/${bill.houseId}/${bill.id}`;
      try {
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(mockUrl);
        }
      } catch {
        // Fallback when clipboard permissions are unavailable in local preview
      }
      pushToast(
        `Link do ${bill.number} copiado para a área de transferência!`,
        'info',
      );
    },
    [pushToast],
  );

  const handleOpenCommunity = useCallback((houseId: string | null) => {
    setSelectedHouseId(houseId);
    setActiveTab('communities');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleOpenPolitician = useCallback((politicianId: string) => {
    setProfileTarget({ type: 'politician', id: politicianId });
    setActiveTab('profile');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleOpenParty = useCallback((partyAcronym: string) => {
    setProfileTarget({ type: 'party', acronym: partyAcronym });
    setActiveTab('profile');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleSelectTab = useCallback((tab: NavigationTab) => {
    if (tab !== 'communities') {
      setSelectedHouseId(null);
    }
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const handleOpenAccount = useCallback(() => {
    setActiveTab(currentUser ? 'account' : 'auth');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [currentUser]);

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A]">
      <Navbar
        activeTab={activeTab}
        onSelectTab={handleSelectTab}
        followedCount={followedHouseIds.length}
        onOpenDrawer={() => setIsDrawerOpen(true)}
        userEmail={currentUser?.email ?? null}
        onOpenAccount={handleOpenAccount}
      />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {activeTab === 'auth' && (
          <AuthPage
            onLogin={handleLogin}
            onRegister={handleRegister}
            onContinueAsGuest={() => handleSelectTab('feed')}
          />
        )}

        {activeTab === 'account' && currentUser && (
          <AccountSettingsPage
            account={currentUser}
            houses={LEGISLATIVE_HOUSES}
            followedHouseIds={followedHouseIds}
            onUpdateEmail={handleUpdateEmail}
            onUpdatePassword={handleUpdatePassword}
            onUpdateNotifications={handleUpdateNotifications}
            onToggleFollow={handleToggleFollow}
            onLogout={handleLogout}
          />
        )}

        {activeTab === 'account' && !currentUser && (
          <AuthPage
            onLogin={handleLogin}
            onRegister={handleRegister}
            onContinueAsGuest={() => handleSelectTab('feed')}
          />
        )}

        {activeTab === 'feed' && (
          <FeedPage
            bills={MOCK_BILLS}
            houses={LEGISLATIVE_HOUSES}
            followedHouseIds={followedHouseIds}
            voteAlertsEnabled={voteAlertsEnabled}
            userVotes={userVotes}
            likedBillIds={likedBillIds}
            onVote={handleVote}
            onToggleLike={handleToggleLike}
            onShare={handleShare}
            onSelectHouse={(id) => handleOpenCommunity(id)}
            onSelectPolitician={handleOpenPolitician}
            onSelectParty={handleOpenParty}
          />
        )}

        {activeTab === 'communities' && (
          <CommunitiesPage
            houses={LEGISLATIVE_HOUSES}
            bills={MOCK_BILLS}
            politicians={MOCK_POLITICIANS}
            followedHouseIds={followedHouseIds}
            selectedHouseId={selectedHouseId}
            userVotes={userVotes}
            likedBillIds={likedBillIds}
            onSelectHouse={setSelectedHouseId}
            onToggleFollow={handleToggleFollow}
            onVote={handleVote}
            onToggleLike={handleToggleLike}
            onShare={handleShare}
            onSelectPolitician={handleOpenPolitician}
            onSelectParty={handleOpenParty}
          />
        )}

        {activeTab === 'profile' && (
          <PoliticianProfilePage
            target={profileTarget}
            politicians={MOCK_POLITICIANS}
            parties={MOCK_PARTIES}
            bills={MOCK_BILLS}
            houses={LEGISLATIVE_HOUSES}
            onSelectTarget={setProfileTarget}
            onSelectHouse={(id) => handleOpenCommunity(id)}
            onOpenBillInFeed={() => handleSelectTab('feed')}
          />
        )}

        {activeTab === 'dashboard' && (
          <DashboardPage
            houses={LEGISLATIVE_HOUSES}
            bills={MOCK_BILLS}
            userVotes={userVotes}
            onSelectHouse={(id) => handleOpenCommunity(id)}
            onSelectParty={handleOpenParty}
          />
        )}
      </main>

      <footer className="mt-12 border-t border-[#E2E8F0] bg-white py-6 text-center text-xs text-slate-500">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <p className="font-semibold text-[#002776]">
            Quorum · Plataforma Cívica de Transparência Legislativa (Brasil)
          </p>
          <p className="mt-1">
            Arquitetura limpa, sem ruído social e orientada a dados públicos oficiais e linguagem cidadã.
          </p>
        </div>
      </footer>

      <FollowedDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        houses={LEGISLATIVE_HOUSES}
        followedHouseIds={followedHouseIds}
        voteAlertsEnabled={voteAlertsEnabled}
        onToggleFollow={handleToggleFollow}
        onToggleVoteAlerts={() => {
          setVoteAlertsEnabled((prev) => {
            const next = !prev;
            if (currentUser) {
              const updatedUser: UserAccount = {
                ...currentUser,
                notifications: {
                  ...currentUser.notifications,
                  urgentVoteAlerts: next,
                },
              };
              setCurrentUser(updatedUser);
              setRegisteredAccounts((accs) =>
                accs.map((acc) =>
                  acc.email === currentUser.email ? updatedUser : acc,
                ),
              );
            }
            pushToast(
              next
                ? 'Alertas de votação ativados no topo do feed.'
                : 'Alertas de votação pausados.',
              'info',
            );
            return next;
          });
        }}
        onOpenCommunity={(id) => handleOpenCommunity(id)}
      />

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
};

export default App;
