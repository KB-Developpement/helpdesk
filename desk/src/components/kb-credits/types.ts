// Shapes returned by kb_credits/api.py. Kept in one place so a backend change
// surfaces as a type error here rather than as a silently blank panel.

import type { SlaDegradationFields } from "@/components/kb-credits-portal/types";

export type AlertLevel = "ok" | "warning" | "danger";

/** kb_credits.api.get_account_summary */
export interface AccountSummary extends SlaDegradationFields {
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
  /** planned intervention time: it alone sets the after-hours multiplier */
  intervention_at?: string | null;
  announced_weight: number;
  final_weight: number;
  /** 1 once a final weight is set (layer contest, requalification, settlement) */
  has_final_weight?: 0 | 1;
  status: QualificationStatus;
  requires_validation: 0 | 1;
  announced_on?: string;
  tacit_deadline?: string;
  /** set when the customer was actually notified (email sent or portal view) */
  customer_notified_on?: string | null;
  notified_via?: string | null;
  validation_mode?: string | null;
  /** true while the 48 h tacit clock is on hold (customer not notified yet) */
  awaiting_notification?: boolean;
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
  /** RB-1 threshold (KB Credit Settings.validation_threshold); UI falls back to 1 */
  validation_threshold?: number;
}

/**
 * kb_credits.api.get_grid — one row of Annexe A.
 *
 * The server historically returned `weight` / `quote_only`; `base_weight` /
 * `on_quote` are aliases added later. Always read through the helpers in
 * grid.ts, never the raw fields, so either shape works.
 */
export interface GridCode {
  code: string;
  label: string;
  category?: string;
  weight?: number;
  base_weight?: number;
  is_free?: boolean | 0 | 1;
  /** F4-style code: the agent must estimate a weight between min and max */
  is_range?: boolean | 0 | 1;
  min_weight?: number;
  max_weight?: number;
  quote_only?: boolean | 0 | 1;
  on_quote?: boolean | 0 | 1;
  description?: string;
}

/** kb_credits.api.get_responsibility_layers */
export interface ResponsibilityLayer {
  layer: string;
  factor: number;
  label: string;
}
