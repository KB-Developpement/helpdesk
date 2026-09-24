// Formatting and rule helpers shared by the customer "My credits" page, the
// customer ticket sidebar block and the agent credits dashboard.
//
// The action rules below mirror kb_credits/qualification.py and statements.py:
// the server remains the only authority (it re-checks everything), the UI only
// avoids offering a button the server would refuse.

import { __ } from "@/translation";
import { dayjs } from "frappe-ui";
import { formatCredits } from "./format";
import type { PortalQualification, SlaDegradationFields, Statement } from "./types";

// Les formats d'affichage (nombres, dates, pourcentages à la française) vivent
// dans format.ts, partagé avec le panneau agent ; réexportés ici pour ne pas
// casser les imports existants.
export {
  formatCredits,
  formatDA,
  formatDate,
  formatDateTime,
  formatLongDate,
  formatNumber,
  formatPercent,
  formatSignedCredits,
  frenchifyText,
  fromNowFr,
} from "./format";

// ---------------------------------------------------------------------------
// SLA dégradé (art. 5.7) : packs L / XL sans exercice d'astreinte co-signé
// ---------------------------------------------------------------------------

/** Packs dont le SLA nominal suppose l'exercice d'astreinte (art. 5.7). */
const STANDBY_PACKS = ["L", "XL"];
const DEGRADED_SUFFIX = "-DEG";

/**
 * Le compte tourne-t-il sous SLA dégradé (KB L-DEG / KB XL-DEG : P1 à 8 h
 * ouvrées) ? Lit, par ordre de fiabilité : le drapeau explicite du serveur
 * (`sla_degraded`), le nom du SLA appliqué (`sla` / `kb_pack` en « -DEG »),
 * puis l'état de l'exercice d'astreinte d'un pack L/XL (`standby_test_done`).
 * Sans aucune de ces informations, on ne suppose rien.
 */
export function isSlaDegraded(s: SlaDegradationFields | null | undefined): boolean {
  if (!s) return false;
  if (s.sla_degraded !== undefined && s.sla_degraded !== null)
    return Boolean(Number(s.sla_degraded));
  for (const name of [s.sla, s.kb_pack]) {
    if (typeof name === "string" && name.trim().toUpperCase().endsWith(DEGRADED_SUFFIX))
      return true;
  }
  // un compte « Recharge » n'a pas de pack ; « Dotation incluse » L/XL suit la règle des packs
  if (s.account_type === "Recharge") return false;
  if (s.standby_test_done !== undefined && s.standby_test_done !== null) {
    const pack = String(s.pack || "").trim().toUpperCase();
    return STANDBY_PACKS.includes(pack) && !Number(s.standby_test_done);
  }
  return false;
}

export function isPast(d: string | null | undefined): boolean {
  return Boolean(d) && dayjs(d).isBefore(dayjs());
}

/** frappe-ui call() errors carry server messages in `messages`. */
export function errorText(e: any): string {
  if (!e) return "";
  if (Array.isArray(e.messages) && e.messages.length) return e.messages.join(", ");
  return e.message || String(e);
}

/** Errors that mean "kb_credits is not usable here": stay silent. */
export function isSilentError(e: any): boolean {
  return /not found|does not exist|AttributeError|Method Not Allowed|PermissionError|not whitelisted|Aucun client/i.test(
    errorText(e) + " " + (e?.exc_type || "")
  );
}

// ---------------------------------------------------------------------------
// What the customer may do on a qualification line
// ---------------------------------------------------------------------------

/** qualification.validate_qualification only accepts "Annoncée". */
export function canValidate(q: PortalQualification): boolean {
  return q.status === "Annoncée";
}

/** qualification.contest_qualification accepts "Annoncée" and "Validée". */
export function canContestWeight(q: PortalQualification): boolean {
  return q.status === "Annoncée" || q.status === "Validée";
}

/**
 * Art. 4.2: the layer may be contested during 5 working days, on a precise
 * technical element. Not offered once the line is settled, cancelled, on
 * quote or free (a free line has nothing left to reduce).
 */
export function canContestLayer(q: PortalQualification): boolean {
  if (q.layer_locked) return false;
  if (q.is_free) return false;
  if (["Brouillon", "Décomptée", "Annulée", "Sur devis"].includes(q.status))
    return false;
  if (q.layer_contest_deadline && isPast(q.layer_contest_deadline)) return false;
  return true;
}

/**
 * A final weight has been set: settled line, layer contest (art. 4.2) or
 * downward requalification. The announced weight then only stays the ceiling.
 */
export function hasFinalWeight(q: Partial<PortalQualification>): boolean {
  return q.status === "Décomptée" || Boolean(Number(q.has_final_weight || 0));
}

/** The weight the customer should read: the final one once set, announced before. */
export function displayedWeight(q: Partial<PortalQualification>): number {
  if (hasFinalWeight(q)) return Number(q.final_weight || 0);
  return Number(q.announced_weight || 0);
}

/**
 * How the displayed weight was built: base × multiplier × layer [× surcharge].
 * Always ends on the displayed weight, so the equation adds up; a line capped
 * by its announced ceiling says so. Empty when nothing changed the grid weight.
 */
export function weightBreakdown(q: Partial<PortalQualification>): string {
  if (q.is_free) return "";
  const base = Number(q.base_weight || 0);
  const mult = Number(q.multiplier || 1);
  // without a layer the factor is meaningless (and may be stored as 0)
  const layer = q.responsibility_layer ? Number(q.layer_factor ?? 1) : 1;
  const result = displayedWeight(q);
  const parts = [formatCredits(base)];
  if (mult !== 1) parts.push(__("× {0} (outside working hours)", formatCredits(mult)));
  if (layer !== 1) parts.push(__("× {0} (responsibility layer)", formatCredits(layer)));
  let product = base * mult * layer;
  if (q.unfounded_p1 && product > 0 && result > product + 0.005) {
    const surcharge = result / product;
    parts.push(__("× {0} (unfounded P1 surcharge)", formatCredits(surcharge)));
    product = result;
  }
  const rounded = Math.round(product * 100) / 100;
  if (parts.length === 1 && Math.abs(rounded - result) < 0.005) return "";
  let text = parts.join(" ") + " = " + formatCredits(rounded);
  if (Math.abs(rounded - result) >= 0.005)
    text += " — " + __("capped at the announced weight: {0}", formatCredits(result));
  return text;
}

export function qualificationTheme(status: string): string {
  switch (status) {
    case "Validée":
    case "Acceptation tacite":
      return "green";
    case "Annoncée":
      return "orange";
    case "Contestée":
      return "red";
    case "Décomptée":
      return "blue";
    default:
      return "gray";
  }
}

export function statementTheme(status: string): string {
  switch (status) {
    case "Émis":
      return "orange";
    case "Réputé accepté":
    case "Réglé":
      return "green";
    case "Contesté":
      return "red";
    default:
      return "gray";
  }
}

/** statements.contest_statement only accepts "Émis". */
export function canContestStatement(s: Statement): boolean {
  return s.status === "Émis";
}

export function movementTheme(credits: number): string {
  if (credits > 0) return "text-ink-green-3";
  if (credits < 0) return "text-ink-gray-9";
  return "text-ink-gray-5";
}
