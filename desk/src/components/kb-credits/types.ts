// Shapes returned by kb_credits/api.py. Kept in one place so a backend change
// surfaces as a type error here rather than as a silently blank panel.

export type AlertLevel = "ok" | "warning" | "danger";

/** kb_credits.api.get_account_summary */
export interface AccountSummary {
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
  consumed?: number;
  balance?: number;
  consumption_pct?: number;
  remedy_credits?: number;
  remedy_cap?: number;
  symmetry_credits?: number;
  alert_level?: AlertLevel;
  thresholds?: { warning: number; danger: number };
}

/** Status values come from the KB Ticket Qualification doctype (French, by design). */
export type QualificationStatus =
  | "Brouillon"
  | "Annoncée"
  | "Validée"
  | "Acceptation tacite"
  | "Contestée"
  | "Décomptée"
  | "Sur devis"
  | "Annulée";

/** One row of kb_credits.api.get_ticket_credits -> qualifications */
export interface Qualification {
  name: string;
  grid_code: string;
  grid_label: string;
  category: string;
  base_weight: number;
  multiplier: number;
  announced_weight: number;
  final_weight: number;
  status: QualificationStatus;
  requires_validation: 0 | 1;
  announced_on?: string;
  tacit_deadline?: string;
  announced_balance?: number;
  contest_reason?: string;
  resolution_note?: string;
  downgraded_from?: string;
  is_free: 0 | 1;
  ledger_entry?: string;
  responsibility_layer?: string;
  layer_factor?: number;
  layer_contest_deadline?: string;
  layer_locked: 0 | 1;
  is_regularisation: 0 | 1;
  unfounded_p1: 0 | 1;
  onsite: 0 | 1;
  travel_fee?: number;
  surcharge_note?: string;
}

/** kb_credits.api.get_ticket_credits */
export interface TicketCredits {
  customer: string;
  qualifications: Qualification[];
  announced_total: number;
  settled_total: number;
  on_quote: boolean;
  legal_p1: boolean;
  legal_deadline?: string;
  priority?: string;
  summary: AccountSummary;
  can_qualify: boolean;
  is_manager: boolean;
}

/** kb_credits.api.get_grid */
export interface GridCode {
  code: string;
  label: string;
  base_weight: number;
  category?: string;
}

/** kb_credits.api.get_responsibility_layers */
export interface ResponsibilityLayer {
  layer: string;
  factor: number;
  label: string;
}
