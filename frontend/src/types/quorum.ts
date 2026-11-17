// Strict English codebase types for the Quorum legislative transparency platform.

export type LegislativeSphere = 'Federal' | 'Estadual' | 'Municipal';

export type BillStatus = 'Em Tramitação' | 'Votação Agendada' | 'Aprovado';

export type VoteOption = 'favor' | 'against';

export type OfficialVoteChoice = 'Sim' | 'Não' | 'Abstenção';

export type NavigationTab =
  | 'feed'
  | 'communities'
  | 'profile'
  | 'dashboard'
  | 'account'
  | 'auth';

export interface UserNotificationSettings {
  urgentVoteAlerts: boolean;
  emailDigest: boolean;
  statusChangeNotifications: boolean;
}

export interface UserAccount {
  email: string;
  passwordHash: string;
  createdAt: string;
  notifications: UserNotificationSettings;
}

export type ProfileViewTarget =
  | { type: 'politician'; id: string }
  | { type: 'party'; acronym: string };

export interface PartySeat {
  partyAcronym: string;
  partyName: string;
  seats: number;
  color: string;
  spectrum: string;
  officialUrl: string;
}

export interface LegislativeSession {
  id: string;
  date: string;
  time: string;
  title: string;
  type: string;
  highlightedBills: string[];
}

export interface LegislativeHouse {
  id: string;
  name: string;
  shortName: string;
  sphere: LegislativeSphere;
  stateOrCity: string;
  description: string;
  totalSeats: number;
  followersCount: number;
  isFollowedByDefault: boolean;
  officialPortalUrl: string;
  partyComposition: PartySeat[];
  upcomingSessions: LegislativeSession[];
}

export interface Bill {
  id: string;
  number: string;
  title: string;
  theme: string;
  houseId: string;
  houseShortName: string;
  sphere: LegislativeSphere;
  authorId: string;
  authorName: string;
  authorParty: string;
  authorState: string;
  status: BillStatus;
  nextVoteDate: string;
  isUrgentVote: boolean;
  formalSummary: string;
  aiSummaryBullets: [string, string, string];
  votesInFavor: number;
  votesAgainst: number;
  likesCount: number;
  officialApprovalRate?: number;
}

export interface PoliticianVoteRecord {
  billId: string;
  billNumber: string;
  billTitle: string;
  houseShortName: string;
  date: string;
  officialVote: OfficialVoteChoice;
  citizenMajorityVote: 'A Favor' | 'Contra';
}

export interface Politician {
  id: string;
  name: string;
  role: string;
  partyAcronym: string;
  partyName: string;
  stateOrCity: string;
  houseId: string;
  houseShortName: string;
  legislature: string;
  officialPortalUrl: string;
  attendanceRate: string;
  biographySummary: string;
  authoredBillIds: string[];
  votingHistory: PoliticianVoteRecord[];
}

export interface PartyInfo {
  acronym: string;
  name: string;
  registrationNumber: number;
  foundationYear: number;
  spectrum: string;
  programSummary: string;
  officialPortalUrl: string;
  color: string;
}

export interface ToastNotification {
  id: string;
  message: string;
  variant: 'success' | 'info' | 'warning';
}
