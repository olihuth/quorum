/// <reference types="vite/client" />

import { MOCK_PARTIES } from '../data/mockData';
import {
  Bill,
  BillStatus,
  LegislativeHouse,
  LegislativeSphere,
  OfficialVoteChoice,
  PartyInfo,
  Politician,
  PoliticianVoteRecord,
  UserNotificationSettings,
  VoteOption,
} from '../types/quorum';

const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface ApiPartyComposition {
  party: string;
  party_name: string;
  seat_count: number;
  percentage: number;
  color_hex: string;
}

interface ApiSession {
  id: string;
  date: string;
  time: string;
  title: string;
  type: string;
  highlighted_bills?: string[];
}

interface ApiHouse {
  id: number;
  name: string;
  short_name: string;
  slug: string;
  level: string;
  state_or_city: string;
  total_seats: number;
  followers_count: number;
  is_followed_by_default: boolean;
  official_portal_url: string;
  description: string;
  upcoming_sessions: ApiSession[];
  party_composition: ApiPartyComposition[];
}

interface ApiPoliticianSummary {
  id: number;
  external_id: string;
  name: string;
  state: string;
  role: string;
  party_acronym: string;
  party_name: string;
  party_color_hex: string;
  house_slug: string;
  house_short_name: string;
  legislature: string;
  attendance_rate: string;
  biography_summary: string;
  photo_url?: string | null;
  official_portal_url: string;
  is_active: boolean;
}

interface ApiPoliticianDetail extends ApiPoliticianSummary {
  authored_bills: Array<{
    id: number;
    number: string;
    title: string;
    status: string;
    house_short_name: string;
  }>;
  voting_history: Array<{
    bill_id: number;
    bill_number: string;
    bill_title: string;
    house_short_name: string;
    date_label: string;
    vote_choice: string;
    citizen_majority_vote: 'A Favor' | 'Contra';
  }>;
}

interface ApiBill {
  id: number;
  external_id: string;
  number: string;
  year: number;
  title: string;
  theme: string;
  house_slug: string;
  house_short_name: string;
  level: string;
  author_id?: number | null;
  author_name?: string | null;
  author_party?: string | null;
  author_state?: string | null;
  official_summary: string;
  desjuridiques_summary: string[];
  status: string;
  next_vote_at?: string | null;
  is_urgent_vote: boolean;
  likes_count: number;
  votes_favor: number;
  votes_against: number;
  official_approval_rate?: number | null;
}

export interface ApiVoteResponse {
  bill_id: number;
  choice: VoteOption;
  source: string;
  votes_favor: number;
  votes_against: number;
  total_votes: number;
  favor_percentage: number;
  against_percentage: number;
  message: string;
}

export interface ApiUserProfile {
  id: number;
  email: string;
  urgent_vote_alerts: boolean;
  email_digest: boolean;
  status_change_notifications: boolean;
  followed_house_slugs: string[];
  created_at: string;
}

export interface ApiAuthResponse {
  access_token: string;
  token_type: string;
  user: ApiUserProfile;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function mapLevelToSphere(level: string): LegislativeSphere {
  if (level === 'federal') return 'Federal';
  if (level === 'municipal') return 'Municipal';
  return 'Estadual';
}

function mapBillStatus(status: string): BillStatus {
  if (status === 'Aprovado') return 'Aprovado';
  if (status === 'Votação Agendada') return 'Votação Agendada';
  return 'Em Tramitação';
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = `Erro HTTP ${response.status}`;
    try {
      const errorData = await response.json();
      if (typeof errorData?.detail === 'string') {
        detail = errorData.detail;
      }
    } catch {
      // Keep generic HTTP error message if response body is not JSON
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

export async function fetchInitialData(): Promise<{
  houses: LegislativeHouse[];
  bills: Bill[];
  politicians: Politician[];
  parties: PartyInfo[];
}> {
  const [apiHouses, apiBills, apiPoliticians] = await Promise.all([
    requestJson<ApiHouse[]>('/houses'),
    requestJson<ApiBill[]>('/bills'),
    requestJson<ApiPoliticianSummary[]>('/politicians'),
  ]);

  const houses: LegislativeHouse[] = apiHouses.map((h) => ({
    id: h.slug,
    name: h.name,
    short_name_unused: undefined,
    shortName: h.short_name,
    sphere: mapLevelToSphere(h.level),
    stateOrCity: h.state_or_city,
    description: h.description,
    totalSeats: h.total_seats,
    followersCount: h.followers_count,
    isFollowedByDefault: h.is_followed_by_default,
    officialPortalUrl: h.official_portal_url,
    upcomingSessions: (h.upcoming_sessions || []).map((s) => ({
      id: s.id,
      date: s.date,
      time: s.time,
      title: s.title,
      type: s.type,
      highlightedBills: s.highlighted_bills || [],
    })),
    partyComposition: (h.party_composition || []).map((p) => ({
      partyAcronym: p.party,
      partyName: p.party_name,
      seats: p.seat_count,
      color: p.color_hex,
      spectrum: 'Diversos',
      officialUrl: h.official_portal_url,
    })),
  })).map(({ short_name_unused: _, ...rest }) => rest);

  const politicianByBackendId = new Map<number, Politician>();
  const politicians: Politician[] = apiPoliticians.map((p) => {
    const mapped: Politician = {
      id: p.external_id,
      backendId: p.id,
      name: p.name,
      role: p.role,
      partyAcronym: p.party_acronym,
      partyName: p.party_name,
      stateOrCity: p.state,
      houseId: p.house_slug,
      houseShortName: p.house_short_name,
      legislature: p.legislature,
      photoUrl: p.photo_url ?? undefined,
      officialPortalUrl: p.official_portal_url,
      attendanceRate: p.attendance_rate,
      biographySummary: p.biography_summary,
      authoredBillIds: [],
      votingHistory: [],
    };
    politicianByBackendId.set(p.id, mapped);
    return mapped;
  });

  const bills: Bill[] = apiBills.map((b) => {
    const bullets = b.desjuridiques_summary ?? [];
    const safeBullets: [string, string, string] = [
      bullets[0] || b.title,
      bullets[1] || b.official_summary,
      bullets[2] || 'Acompanhe os desdobramentos desta proposição no Quorum.',
    ];

    const linkedAuthor = b.author_id
      ? politicianByBackendId.get(b.author_id)
      : undefined;
    if (linkedAuthor) {
      linkedAuthor.authoredBillIds.push(b.external_id);
    }

    return {
      id: b.external_id,
      backendId: b.id,
      number: b.number,
      title: b.title,
      theme: b.theme,
      houseId: b.house_slug,
      houseShortName: b.house_short_name,
      sphere: mapLevelToSphere(b.level),
      authorId: linkedAuthor?.id ?? '',
      authorName: b.author_name ?? linkedAuthor?.name ?? 'Autoria Parlamentar',
      authorParty: b.author_party ?? linkedAuthor?.partyAcronym ?? '—',
      authorState: b.author_state ?? linkedAuthor?.stateOrCity ?? 'BR',
      status: mapBillStatus(b.status),
      nextVoteDate: b.next_vote_at ?? 'Sem data definida',
      isUrgentVote: b.is_urgent_vote,
      formalSummary: b.official_summary,
      aiSummaryBullets: safeBullets,
      votesInFavor: b.votes_favor,
      votesAgainst: b.votes_against,
      likesCount: b.likes_count,
      officialApprovalRate: b.official_approval_rate ?? undefined,
    };
  });

  // Merge rich mock party metadata with any real parties synced in backend
  const partyMap = new Map<string, PartyInfo>();
  for (const mockParty of MOCK_PARTIES) {
    partyMap.set(mockParty.acronym, mockParty);
  }
  for (const pol of apiPoliticians) {
    if (!partyMap.has(pol.party_acronym)) {
      partyMap.set(pol.party_acronym, {
        acronym: pol.party_acronym,
        name: pol.party_name,
        registrationNumber: 0,
        foundationYear: 0,
        spectrum: 'Bancada Oficial',
        programSummary:
          'Bancada parlamentar com dados sincronizados diretamente das APIs oficiais da Câmara e do Senado.',
        officialPortalUrl: 'https://www.tse.jus.br/partidos/partidos-registrados-no-tse',
        color: pol.party_color_hex || '#64748B',
      });
    }
  }
  for (const house of houses) {
    for (const comp of house.partyComposition) {
      if (comp.partyAcronym !== 'Outros' && !partyMap.has(comp.partyAcronym)) {
        partyMap.set(comp.partyAcronym, {
          acronym: comp.partyAcronym,
          name: comp.partyName,
          registrationNumber: 0,
          foundationYear: 0,
          spectrum: 'Bancada Oficial',
          programSummary:
            'Bancada parlamentar com dados sincronizados diretamente das APIs oficiais da Câmara e do Senado.',
          officialPortalUrl: 'https://www.tse.jus.br/partidos/partidos-registrados-no-tse',
          color: comp.color || '#64748B',
        });
      }
    }
  }

  return {
    houses,
    bills,
    politicians,
    parties: Array.from(partyMap.values()),
  };
}

export async function fetchPoliticianDetail(
  backendId: number,
  bills: Bill[],
): Promise<{
  authoredBillIds: string[];
  votingHistory: PoliticianVoteRecord[];
}> {
  const detail = await requestJson<ApiPoliticianDetail>(`/politicians/${backendId}`);
  const billByBackendId = new Map(
    bills.filter((b) => b.backendId !== undefined).map((b) => [b.backendId!, b]),
  );

  const authoredBillIds = detail.authored_bills
    .map((ab) => billByBackendId.get(ab.id)?.id)
    .filter((id): id is string => Boolean(id));

  const votingHistory: PoliticianVoteRecord[] = detail.voting_history.map((vh) => ({
    billId: billByBackendId.get(vh.bill_id)?.id ?? String(vh.bill_id),
    billNumber: vh.bill_number,
    billTitle: vh.bill_title,
    houseShortName: vh.house_short_name,
    date: vh.date_label,
    officialVote: (vh.vote_choice as OfficialVoteChoice) || 'Sim',
    citizenMajorityVote: vh.citizen_majority_vote,
  }));

  return { authoredBillIds, votingHistory };
}

export async function submitBillVote(
  billBackendId: number,
  citizenIdentifier: string,
  choice: VoteOption,
): Promise<ApiVoteResponse> {
  return requestJson<ApiVoteResponse>(`/bills/${billBackendId}/vote`, {
    method: 'POST',
    body: JSON.stringify({
      citizen_identifier: citizenIdentifier,
      choice,
    }),
  });
}

export async function submitBillLike(
  billBackendId: number,
): Promise<{ bill_id: number; likes_count: number }> {
  return requestJson<{ bill_id: number; likes_count: number }>(
    `/bills/${billBackendId}/like`,
    { method: 'POST' },
  );
}

export async function registerUserApi(
  email: string,
  password: string,
): Promise<ApiAuthResponse> {
  return requestJson<ApiAuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function loginUserApi(
  email: string,
  password: string,
): Promise<ApiAuthResponse> {
  return requestJson<ApiAuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function updateUserSettingsApi(
  token: string,
  payload: {
    email?: string;
    current_password?: string;
    new_password?: string;
    notifications?: Partial<UserNotificationSettings>;
    followed_house_slugs?: string[];
  },
): Promise<ApiUserProfile> {
  return requestJson<ApiUserProfile>('/users/me', {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      email: payload.email,
      current_password: payload.current_password,
      new_password: payload.new_password,
      urgent_vote_alerts: payload.notifications?.urgentVoteAlerts,
      email_digest: payload.notifications?.emailDigest,
      status_change_notifications: payload.notifications?.statusChangeNotifications,
      followed_house_slugs: payload.followed_house_slugs,
    }),
  });
}
