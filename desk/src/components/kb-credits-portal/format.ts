// Formats d'affichage français partagés par tout l'écran « crédits
// d'intervention » : portail client (kb-credits-portal), panneau agent
// (kb-credits) et tableau de bord agent.
//
// Règle : on n'affiche jamais un nombre ou une date brute du serveur
// (600.0, 2026-09-01, 0.3 %) ; tout passe par ces fonctions.

import { dayjs } from "frappe-ui";
// Charge la locale fr dans l'instance dayjs de frappe-ui (même module ESM),
// sans la rendre globale : chaque appel choisit sa locale explicitement.
import "dayjs/esm/locale/fr";

const numberFormatters = new Map<number, Intl.NumberFormat>();

function numberFormatter(maxFractionDigits: number): Intl.NumberFormat {
  let f = numberFormatters.get(maxFractionDigits);
  if (!f) {
    f = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: maxFractionDigits });
    numberFormatters.set(maxFractionDigits, f);
  }
  return f;
}

function isBlank(n: unknown): boolean {
  return n === null || n === undefined || n === "" || Number.isNaN(Number(n));
}

/** 600.0 -> "600" ; 1234.5 -> "1 234,5". */
export function formatNumber(n: number | string | null | undefined, maxFractionDigits = 2): string {
  if (isBlank(n)) return "–";
  return numberFormatter(maxFractionDigits).format(Number(n));
}

/** 1.5 -> "1,5" ; 2 -> "2". Credits move in 0.25 steps. */
export function formatCredits(n: number | string | null | undefined): string {
  return formatNumber(n, 2);
}

/** Signed variant for ledger movements: "+2", "−1,5", "0". */
export function formatSignedCredits(n: number | null | undefined): string {
  if (isBlank(n)) return "–";
  const v = Number(n);
  if (v > 0) return "+" + formatNumber(v);
  if (v < 0) return "−" + formatNumber(Math.abs(v));
  return "0";
}

/** 0.3 -> "0,3 %" (espace insécable, typographie française). */
export function formatPercent(n: number | string | null | undefined, maxFractionDigits = 1): string {
  if (isBlank(n)) return "–";
  return formatNumber(n, maxFractionDigits) + " %";
}

/** Travel fees are in dinars, never in credits. */
export function formatDA(n: number | null | undefined): string {
  if (!n) return "";
  return formatNumber(n, 0) + " DA";
}

/** "2026-09-01" -> "01/09/2026". */
export function formatDate(d: string | null | undefined): string {
  if (!d) return "";
  const v = dayjs(d);
  return v.isValid() ? v.format("DD/MM/YYYY") : String(d);
}

/** "2026-09-01 14:05:00" -> "01/09/2026 14:05". */
export function formatDateTime(d: string | null | undefined): string {
  if (!d) return "";
  const v = dayjs(d);
  return v.isValid() ? v.format("DD/MM/YYYY HH:mm") : String(d);
}

/** "2026-09-01" -> "1 sept. 2026". */
export function formatLongDate(d: string | null | undefined): string {
  if (!d) return "";
  const v = dayjs(d);
  return v.isValid() ? v.locale("fr").format("D MMM YYYY") : String(d);
}

/** Relative time in French: "dans 5 jours", "il y a 2 heures". */
export function fromNowFr(d: string | Date | null | undefined, withoutSuffix = false): string {
  if (!d) return "";
  const v = dayjs.tz(d as any);
  return v.isValid() ? v.locale("fr").fromNow(withoutSuffix) : "";
}

/** Full date in French for tooltips: "mardi 29 septembre 2026 14:00". */
export function formatFullDateFr(d: string | Date | null | undefined): string {
  if (!d) return "";
  const v = dayjs(d as any);
  return v.isValid() ? v.locale("fr").format("dddd D MMMM YYYY HH:mm") : "";
}

/**
 * Libellés rédigés côté serveur (motif d'un mouvement, note de majoration…) :
 * ils embarquent parfois des dates ISO et des nombres à point décimal
 * (« pack XL (600.0 crédits) du 2026-09-01 au 2027-08-31 »). On ne réécrit
 * que ces deux motifs, sans toucher au reste du texte.
 */
export function frenchifyText(s: string | null | undefined): string {
  if (!s) return "";
  return String(s)
    .replace(/\b(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::\d{2}(?:\.\d+)?)?)?\b/g,
      (_m, y, mo, d, h, mi) => (h ? `${d}/${mo}/${y} ${h}:${mi}` : `${d}/${mo}/${y}`))
    // nombre décimal isolé (pas un numéro de version « v1.2.3 », pas une IP)
    .replace(/(^|[^\w.])(\d+)\.(\d+)(?![\w.])/g, (_m, pre, i, f) => pre + formatNumber(`${i}.${f}`))
    .replace(/(\d)\s?%/g, "$1 %");
}
