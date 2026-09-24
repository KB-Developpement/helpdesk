// Shapes returned by kb_credits/api.py, as consumed by the customer portal
// and the agent dashboard. Declared here (not imported from ../kb-credits) so
// the portal pages keep compiling whatever the agent panel does with its own
// types. Keep in sync with kb_credits/kb_credits/api.py.

export type AlertLevel = "ok" | "warning" | "danger";

/**
 * Ce qui permet de savoir si le SLA du compte est dégradé (art. 5.7). Tous
 * optionnels : le serveur peut n'en renvoyer qu'une partie, voire aucun.
 */
export interface SlaDegradationFields {
  account_type?: string;
  pack?: string;
  /** drapeau explicite, prioritaire */
  sla_degraded?: boolean | number | null;
  /** SLA Helpdesk appliqué, ex. « KB XL-DEG » */
  sla?: string | null;
  kb_pack?: string | null;
  /** exercice d'astreinte co-signé (packs L / XL) */
  standby_test_done?: boolean | number | null;
}

/** kb_credits.api.get_account_summary */
export interface PortalAccountSummary extends SlaDegradationFields {
  has_account: boolean;
  customer: string;
  account?: string;
  account_type?: string;
  pack?: string;
  pack_name?: string;
  grid_version?: string;
  period_start?: string;
  period_end?: string;
  allocated?: number;
  /** crédits servant de base au % consommé : dotation, ou crédits achetés (compte « Recharge ») */
  consumption_base?: number;
  consumed?: number;
  balance?: number;
  consumption_pct?: number;
  remedy_credits?: number;
  remedy_cap?: number;
  symmetry_credits?: number;
  alert_level?: AlertLevel;
  thresholds?: { warning: number; danger: number };
  /** only with include_pending=1 — reading them as a customer counts as notification */
  pending_validations?: PendingValidation[];
  pending_statements?: PendingStatement[];
}

/** get_account_summary(include_pending=1).pending_validations */
export interface PendingValidation {
  name: string;
  ticket: string;
  grid_code: string;
  grid_label?: string | null;
  announced_weight: number;
  requires_validation?: 0 | 1;
  tacit_deadline?: string | null;
}

/** get_account_summary(include_pending=1).pending_statements */
export interface PendingStatement {
  name: string;
  period_start: string;
  period_end: string;
  closing_balance: number;
  acceptance_deadline?: string | null;
}

/** One row of get_ticket_credits().qualifications (French status values by design). */
export interface PortalQualification {
  name: string;
  grid_code: string;
  grid_label?: string;
  category?: string;
  base_weight?: number;
  multiplier?: number;
  announced_weight?: number;
  final_weight?: number;
  /** 1 once a final weight is set (layer contest, requalification, settlement) */
  has_final_weight?: 0 | 1;
  status: string;
  requires_validation?: 0 | 1;
  announced_on?: string | null;
  tacit_deadline?: string | null;
  announced_balance?: number | null;
  contest_reason?: string | null;
  resolution_note?: string | null;
  downgraded_from?: string | null;
  is_free?: 0 | 1;
  ledger_entry?: string | null;
  responsibility_layer?: string | null;
  layer_factor?: number | null;
  layer_contest_deadline?: string | null;
  layer_locked?: 0 | 1;
  is_regularisation?: 0 | 1;
  unfounded_p1?: 0 | 1;
  onsite?: 0 | 1;
  travel_fee?: number | null;
  surcharge_note?: string | null;
  /** added client-side on the "My credits" page */
  ticket?: string;
  ticket_subject?: string;
}

/** kb_credits.api.get_ticket_credits */
export interface PortalTicketCredits {
  customer: string;
  qualifications: PortalQualification[];
  announced_total: number;
  settled_total: number;
  on_quote: boolean;
  legal_p1: boolean;
  legal_deadline?: string | null;
  priority?: string | null;
  summary: PortalAccountSummary;
  can_qualify: boolean;
  is_manager: boolean;
}

/** kb_credits.api.get_movements */
export interface Movement {
  name: string;
  posting_datetime: string;
  entry_type: string;
  credits: number;
  balance_after?: number | null;
  ticket?: string | null;
  grid_code?: string | null;
  reason?: string | null;
  expires_on?: string | null;
}

/** kb_credits.api.get_statements */
export interface Statement {
  name: string;
  statement_type: string;
  period_start: string;
  period_end: string;
  opening_balance: number;
  closing_balance: number;
  /** allocations, recharges and carry-over received */
  total_recharges?: number;
  total_consumed: number;
  total_remedies: number;
  total_symmetry?: number;
  /** signed: adjustments, expirations, carry-over sent to the next account */
  total_adjustments?: number;
  status: string;
  acceptance_deadline?: string | null;
  sla_breaches?: number;
}

/** kb_credits.api.legal_banner (legal.active_windows) */
export interface LegalWindow {
  deadline: string;
  description?: string | null;
  due_date: string;
  window_start: string;
  hours_left: number;
}

/** kb_credits.api.get_responsibility_layers */
export interface LayerOption {
  layer: string;
  factor: number;
  label: string;
}

/** kb_credits.api.agent_dashboard */
export interface DashboardQualification {
  name: string;
  ticket: string;
  customer?: string | null;
  grid_code: string;
  announced_weight: number;
  tacit_deadline?: string | null;
  contest_reason?: string | null;
}

export interface DashboardLegalTicket {
  name: string;
  subject?: string | null;
  customer?: string | null;
  kb_legal_deadline?: string | null;
  priority?: string | null;
}

export interface DashboardAccount {
  name: string;
  customer: string;
  remedy_annual_cap: number;
  remedy_credits_received: number;
  consumption_pct?: number | null;
}

/** kb_credits.api.agent_dashboard().contested_statements */
export interface DashboardStatement {
  name: string;
  customer?: string | null;
  account?: string | null;
  period_start: string;
  period_end: string;
  closing_balance?: number | null;
  contested_on?: string | null;
  contest_reason?: string | null;
}

export interface AgentDashboard {
  pending_validation: DashboardQualification[];
  tacit_imminent: DashboardQualification[];
  contested_statements?: DashboardStatement[];
  contested: DashboardQualification[];
  legal_p1_tickets: DashboardLegalTicket[];
  accounts_near_remedy_cap: DashboardAccount[];
  legal_windows: LegalWindow[];
}
