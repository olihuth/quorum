import React, { useCallback, useEffect, useState } from 'react';
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
  ApiError,
  fetchInitialData,
  fetchPoliticianDetail,
  loginUserApi,
  registerUserApi,
  submitBillLike,
  submitBillVote,
  updateUserSettingsApi,
} from './services/api';
import {
  Bill,
  LegislativeHouse,
  NavigationTab,
  PartyInfo,
  Politician,
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

function getOrCreateGuestIdentifier(): string {
  const storageKey = 'quorum_guest_citizen_id';
  try {
    const existing = window.localStorage.getItem(storageKey);
    if (existing) return existing;
    const generated = `guest-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    window.localStorage.setItem(storageKey, generated);
    return generated;
  } catch {
    return `guest-session-${Math.random().toString(36).slice(2, 10)}`;
  }
}

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('auth');
  const [selectedHouseId, setSelectedHouseId] = useState<string | null>(null);
  const [profileTarget, setProfileTarget] = useState<ProfileViewTarget>({
    type: 'politician',
    id: MOCK_POLITICIANS[0].id,
  });

  // Live Backend Data State (initialized with local fallback until FastAPI responds)
  const [houses, setHouses] = useState<LegislativeHouse[]>(LEGISLATIVE_HOUSES);
  const [bills, setBills] = useState<Bill[]>(MOCK_BILLS);
  const [politicians, setPoliticians] = useState<Politician[]>(MOCK_POLITICIANS);
  const [parties, setParties] = useState<PartyInfo[]>(MOCK_PARTIES);
  const [isBackendConnected, setIsBackendConnected] = useState(false);

  // Private Citizen Account State (no public citizen profile)
  const [registeredAccounts, setRegisteredAccounts] = useState<UserAccount[]>([]);
  const [currentUser, setCurrentUser] = useState<UserAccount | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [guestIdentifier] = useState<string>(() => getOrCreateGuestIdentifier());

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

  // Load real houses, compositions, politicians, and curated bills from FastAPI on mount
  useEffect(() => {
    let active = true;
    fetchInitialData()
      .then((data) => {
        if (!active) return;
        setHouses(data.houses);
        setBills(data.bills);
        setPoliticians(data.politicians);
        setParties(data.parties);
        setIsBackendConnected(true);
        if (data.politicians.length > 0) {
          setProfileTarget((prev) =>
            prev.type === 'politician' &&
            !data.politicians.some((p) => p.id === prev.id)
              ? { type: 'politician', id: data.politicians[0].id }
              : prev,
          );
        }
      })
      .catch(() => {
        // Keep local mock fallback silently if backend server is offline
      });
    return () => {
      active = false;
    };
  }, []);

  // Fetch detailed voting history & authored bills when a politician profile is opened
  useEffect(() => {
    if (!isBackendConnected || profileTarget.type !== 'politician') return;
    const targetPol = politicians.find((p) => p.id === profileTarget.id);
    if (!targetPol?.backendId) return;

    let cancelled = false;
    fetchPoliticianDetail(targetPol.backendId, bills)
      .then((detail) => {
        if (cancelled) return;
        setPoliticians((prev) =>
          prev.map((p) =>
            p.id === targetPol.id
              ? {
                  ...p,
                  authoredBillIds: detail.authoredBillIds,
                  votingHistory: detail.votingHistory,
                }
              : p,
          ),
        );
      })
      .catch(() => {
        // Ignore transient fetch errors
      });
    return () => {
      cancelled = true;
    };
  }, [bills, isBackendConnected, politicians.length, profileTarget]);

  const handleLogin = useCallback(
    async (email: string, password: string): Promise<string | null> => {
      if (isBackendConnected) {
        try {
          const res = await loginUserApi(email, password);
          const loggedAccount: UserAccount = {
            email: res.user.email,
            passwordHash: '',
            createdAt: res.user.created_at,
            notifications: {
              urgentVoteAlerts: res.user.urgent_vote_alerts,
              emailDigest: res.user.email_digest,
              statusChangeNotifications: res.user.status_change_notifications,
            },
          };
          setAuthToken(res.access_token);
          setCurrentUser(loggedAccount);
          setVoteAlertsEnabled(res.user.urgent_vote_alerts);
          if (res.user.followed_house_slugs.length > 0) {
            setFollowedHouseIds(res.user.followed_house_slugs);
          }
          setActiveTab('feed');
          window.scrollTo({ top: 0, behavior: 'smooth' });
          pushToast(`Bem-vindo(a) de volta ao Quorum (${res.user.email})!`, 'success');
          return null;
        } catch (err) {
          if (err instanceof ApiError) {
            return err.message;
          }
          return 'Não foi possível conectar ao servidor de autenticação.';
        }
      }

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
    [isBackendConnected, pushToast, registeredAccounts],
  );

  const handleRegister = useCallback(
    async (email: string, password: string): Promise<string | null> => {
      if (isBackendConnected) {
        try {
          const res = await registerUserApi(email, password);
          const newAccount: UserAccount = {
            email: res.user.email,
            passwordHash: '',
            createdAt: res.user.created_at,
            notifications: {
              urgentVoteAlerts: res.user.urgent_vote_alerts,
              emailDigest: res.user.email_digest,
              statusChangeNotifications: res.user.status_change_notifications,
            },
          };
          setAuthToken(res.access_token);
          setCurrentUser(newAccount);
          setVoteAlertsEnabled(res.user.urgent_vote_alerts);
          setFollowedHouseIds(res.user.followed_house_slugs);
          setActiveTab('feed');
          window.scrollTo({ top: 0, behavior: 'smooth' });
          pushToast(
            'Conta privada criada no servidor! Exibindo suas Casas Seguidas.',
            'success',
          );
          return null;
        } catch (err) {
          if (err instanceof ApiError) {
            return err.message;
          }
          return 'Erro ao registrar conta no servidor.';
        }
      }

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
    [isBackendConnected, pushToast, registeredAccounts],
  );

  const handleLogout = useCallback(() => {
    setCurrentUser(null);
    setAuthToken(null);
    setActiveTab('auth');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    pushToast('Você saiu da sua conta privada.', 'info');
  }, [pushToast]);

  const handleUpdateEmail = useCallback(
    async (newEmail: string): Promise<string | null> => {
      if (!currentUser) return 'Sessão expirada.';
      if (newEmail === currentUser.email) {
        return 'Informe um e-mail diferente do atual.';
      }

      if (isBackendConnected && authToken) {
        try {
          const updated = await updateUserSettingsApi(authToken, { email: newEmail });
          setCurrentUser({ ...currentUser, email: updated.email });
          pushToast('E-mail atualizado com sucesso!', 'success');
          return null;
        } catch (err) {
          return err instanceof ApiError ? err.message : 'Erro ao atualizar e-mail.';
        }
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
    [authToken, currentUser, isBackendConnected, pushToast, registeredAccounts],
  );

  const handleUpdatePassword = useCallback(
    async (currentPassword: string, newPassword: string): Promise<string | null> => {
      if (!currentUser) return 'Sessão expirada.';

      if (isBackendConnected && authToken) {
        try {
          await updateUserSettingsApi(authToken, {
            current_password: currentPassword,
            new_password: newPassword,
          });
          pushToast('Senha atualizada com sucesso!', 'success');
          return null;
        } catch (err) {
          return err instanceof ApiError ? err.message : 'Erro ao atualizar senha.';
        }
      }

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
    [authToken, currentUser, isBackendConnected, pushToast],
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
      if (isBackendConnected && authToken) {
        updateUserSettingsApi(authToken, { notifications: nextNotifications }).catch(() => {
          // Non-blocking sync
        });
      }
      pushToast('Preferências de notificação atualizadas.', 'info');
    },
    [authToken, currentUser, isBackendConnected, pushToast],
  );

  const handleToggleFollow = useCallback(
    (houseId: string) => {
      const house = houses.find((h) => h.id === houseId);
      setFollowedHouseIds((prev) => {
        const alreadyFollowing = prev.includes(houseId);
        const nextList = alreadyFollowing
          ? prev.filter((id) => id !== houseId)
          : [...prev, houseId];

        if (isBackendConnected && authToken) {
          updateUserSettingsApi(authToken, { followed_house_slugs: nextList }).catch(
            () => {},
          );
        }

        pushToast(
          alreadyFollowing
            ? `Você deixou de seguir ${house?.shortName ?? 'esta Casa Legislativa'}.`
            : `Agora você acompanha ${house?.shortName ?? 'esta Casa Legislativa'}!`,
          alreadyFollowing ? 'info' : 'success',
        );
        return nextList;
      });
    },
    [authToken, houses, isBackendConnected, pushToast],
  );

  const handleVote = useCallback(
    async (billId: string, option: VoteOption) => {
      if (userVotes[billId]) return;

      const targetBill = bills.find((b) => b.id === billId);
      if (isBackendConnected && targetBill?.backendId) {
        const citizenIdentifier = currentUser?.email ?? guestIdentifier;
        try {
          const response = await submitBillVote(
            targetBill.backendId,
            citizenIdentifier,
            option,
          );
          setUserVotes((prev) => ({ ...prev, [billId]: option }));
          setBills((prev) =>
            prev.map((b) =>
              b.id === billId
                ? {
                    ...b,
                    votesInFavor: response.votes_favor,
                    votesAgainst: response.votes_against,
                  }
                : b,
            ),
          );
          const label = option === 'favor' ? 'A Favor' : 'Contra';
          pushToast(
            `Voto "${label}" registrado com segurança (LGPD SHA-256)!`,
            'success',
          );
          return;
        } catch (err) {
          if (err instanceof ApiError && err.status === 409) {
            setUserVotes((prev) => ({ ...prev, [billId]: option }));
            pushToast(err.message, 'warning');
            return;
          }
          pushToast(
            err instanceof Error ? err.message : 'Erro ao registrar voto no servidor.',
            'warning',
          );
          return;
        }
      }

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
    [bills, currentUser?.email, guestIdentifier, isBackendConnected, pushToast, userVotes],
  );

  const handleToggleLike = useCallback(
    (billId: string) => {
      const currentlyLiked = likedBillIds.includes(billId);
      const targetBill = bills.find((b) => b.id === billId);

      setLikedBillIds((prev) =>
        currentlyLiked ? prev.filter((id) => id !== billId) : [...prev, billId],
      );

      if (!currentlyLiked && isBackendConnected && targetBill?.backendId) {
        submitBillLike(targetBill.backendId)
          .then((res) => {
            setBills((prev) =>
              prev.map((b) =>
                b.id === billId
                  ? { ...b, likesCount: Math.max(res.likes_count - 1, b.likesCount) }
                  : b,
              ),
            );
          })
          .catch(() => {
            // Non-blocking fallback
          });
      }
    },
    [bills, isBackendConnected, likedBillIds],
  );

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
            houses={houses}
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
            bills={bills}
            houses={houses}
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
            houses={houses}
            bills={bills}
            politicians={politicians}
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
            politicians={politicians}
            parties={parties}
            bills={bills}
            houses={houses}
            onSelectTarget={setProfileTarget}
            onSelectHouse={(id) => handleOpenCommunity(id)}
            onOpenBillInFeed={() => handleSelectTab('feed')}
          />
        )}

        {activeTab === 'dashboard' && (
          <DashboardPage
            houses={houses}
            bills={bills}
            userVotes={userVotes}
            onSelectHouse={(id) => handleOpenCommunity(id)}
            onSelectParty={handleOpenParty}
          />
        )}
      </main>

      <footer className="mt-12 border-t border-[#E2E8F0] bg-white py-6 text-center text-xs text-slate-500">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center justify-center gap-2">
            <p className="font-semibold text-[#002776]">
              Quorum · Plataforma Cívica de Transparência Legislativa (Brasil)
            </p>
            <span className="text-slate-300">·</span>
            <span
              className={`inline-flex items-center gap-1.5 font-medium ${
                isBackendConnected ? 'text-[#009C3B]' : 'text-slate-400'
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isBackendConnected ? 'bg-[#009C3B]' : 'bg-slate-400'
                }`}
                aria-hidden="true"
              />
              {isBackendConnected
                ? 'Conectado à API FastAPI · PostgreSQL 16'
                : 'Modo demonstração local'}
            </span>
          </div>
          <p className="mt-1">
            Arquitetura limpa, sem ruído social e orientada a dados públicos oficiais e linguagem cidadã.
          </p>
        </div>
      </footer>

      <FollowedDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        houses={houses}
        followedHouseIds={followedHouseIds}
        voteAlertsEnabled={voteAlertsEnabled}
        onToggleFollow={handleToggleFollow}
        onToggleVoteAlerts={() => {
          setVoteAlertsEnabled((prev) => {
            const next = !prev;
            if (currentUser) {
              const updatedNotifications = {
                ...currentUser.notifications,
                urgentVoteAlerts: next,
              };
              const updatedUser: UserAccount = {
                ...currentUser,
                notifications: updatedNotifications,
              };
              setCurrentUser(updatedUser);
              setRegisteredAccounts((accs) =>
                accs.map((acc) =>
                  acc.email === currentUser.email ? updatedUser : acc,
                ),
              );
              if (isBackendConnected && authToken) {
                updateUserSettingsApi(authToken, {
                  notifications: updatedNotifications,
                }).catch(() => {});
              }
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
