// Annexe A helpers shared by the announce and requalify dialogs. The server is
// the authority (qualification.resolve_base_weight); these only mirror its rules
// so the agent is told *before* submitting, not by a red error afterwards.
import { formatCredits } from "@/components/kb-credits-portal/format";
import type { GridCode, Qualification } from "./types";

/** Fixed weight of a code; tolerant of both API shapes (weight / base_weight). */
export function gridWeight(g: GridCode | undefined | null): number {
  if (!g) return 0;
  return Number(g.weight ?? g.base_weight ?? 0);
}

export function isRange(g: GridCode | undefined | null): boolean {
  return Boolean(g?.is_range);
}

export function isFree(g: GridCode | undefined | null): boolean {
  return Boolean(g?.is_free);
}

export function isQuoteOnly(g: GridCode | undefined | null): boolean {
  return Boolean(g?.quote_only ?? g?.on_quote);
}

// Formats français partagés avec le portail client (1,5 et non 1.5).
export { formatCredits };

/** Short weight label used in selectors: "2", "6–10", "Free", "On quote". */
export function gridWeightLabel(g: GridCode): string {
  if (isFree(g)) return __("Free");
  if (isQuoteOnly(g)) return __("On quote");
  if (isRange(g))
    return `${formatCredits(g.min_weight)}–${formatCredits(g.max_weight)}`;
  return formatCredits(gridWeight(g));
}

export function gridOptionLabel(g: GridCode): string {
  return `${g.code} — ${g.label} (${gridWeightLabel(g)})`;
}

/** Field description for a range code's estimate. */
export function rangeHintText(g: GridCode | undefined | null): string {
  if (!g || !isRange(g)) return "";
  return __("Between {0} and {1} credits, per Annexe A.")
    .replace("{0}", formatCredits(g.min_weight))
    .replace("{1}", formatCredits(g.max_weight));
}

/**
 * Validates the weight the agent typed for a range code. Returns an error
 * message, or "" when the value is acceptable. Fixed codes never take a
 * value (the server ignores it), so they always pass.
 */
export function rangeWeightError(
  g: GridCode | undefined | null,
  value: string | number | null | undefined
): string {
  if (!g || !isRange(g)) return "";
  const min = Number(g.min_weight ?? 0);
  const max = Number(g.max_weight ?? 0);
  const bounds = __("between {0} and {1} credits")
    .replace("{0}", formatCredits(min))
    .replace("{1}", formatCredits(max));
  if (value === "" || value === null || value === undefined)
    return __("Code {0} requires an estimated weight {1}.")
      .replace("{0}", g.code)
      .replace("{1}", bounds);
  const v = Number(value);
  if (Number.isNaN(v) || v < min || (max > 0 && v > max))
    return __("The estimated weight for {0} must be {1}.")
      .replace("{0}", g.code)
      .replace("{1}", bounds);
  return "";
}

/** Base weight to send to the server: only range codes carry one. */
export function weightParam(
  g: GridCode | undefined | null,
  value: string | number | null | undefined
): number | null {
  if (!isRange(g) || value === "" || value === null || value === undefined)
    return null;
  return Number(value);
}

/**
 * Lowest weight a code can reach once the line's multiplier and layer factor
 * are applied — used to grey out codes that would exceed the announced ceiling
 * (RB-2: requalification only ever goes down).
 */
export function minEffectiveWeight(g: GridCode, q: Qualification): number {
  if (isFree(g)) return 0;
  const base = isRange(g) ? Number(g.min_weight ?? 0) : gridWeight(g);
  const mult = Number(q.multiplier || 1);
  const layer =
    q.layer_factor === undefined || q.layer_factor === null
      ? 1
      : Number(q.layer_factor);
  return Math.round(base * mult * layer * 100) / 100;
}

/** Statuses from which the server accepts a manual settlement (RB-1). */
export const SETTLEABLE_STATUSES = ["Validée", "Acceptation tacite"];

/**
 * Mirrors qualification.settle(): a line is settleable when validated
 * (explicitly or tacitly), or when an announced line is free (D0, E0) or
 * weighs no more than the RB-1 validation threshold. An « Annoncée » line above
 * the threshold is refused by the server, so the button must not be offered.
 * Draft, contested, on-quote and final lines never get it: a contest is the
 * customer disputing the weight, it is resolved by requalification first.
 */
export function canSettle(q: Qualification, validationThreshold = 1): boolean {
  if (SETTLEABLE_STATUSES.includes(q.status)) return true;
  if (q.status !== "Annoncée") return false;
  return (
    Boolean(q.is_free) || Number(q.announced_weight || 0) <= validationThreshold
  );
}
