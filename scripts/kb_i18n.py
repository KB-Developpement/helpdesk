#!/usr/bin/env python3
"""Outils i18n du fork KB du Helpdesk.

Extrait toutes les chaînes passées à __() dans les fichiers de l'interface
KB (crédits d'intervention + pages touchées par codemod_labels.py), puis
confronte le résultat à helpdesk/locale/fr.po.

    python3 scripts/kb_i18n.py check          # liste ce qui manque (code retour 1 si manque)
    python3 scripts/kb_i18n.py refs           # met à jour les références #: des msgids KB
    python3 scripts/kb_i18n.py add FICHIER    # ajoute des traductions (JSON {msgid: msgstr})
    python3 scripts/kb_i18n.py stats          # couverture de fr.po
    ../env/bin/python ../apps/helpdesk/scripts/kb_i18n.py translations SITE
                                              # (depuis sites/) traductions en base contredisant fr.po

Réexécutable après chaque rebase : aucun effet si tout est déjà à jour.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import polib
except ImportError:  # Python du bench : seule la commande `translations` y sert
    polib = None

ROOT = Path(__file__).resolve().parent.parent
PO_PATH = ROOT / "helpdesk" / "locale" / "fr.po"

# Fichiers dont chaque chaîne doit être traduite.
KB_GLOBS = [
    "desk/src/components/kb-credits/**/*.vue",
    "desk/src/components/kb-credits/**/*.ts",
    "desk/src/components/kb-credits-portal/**/*.vue",
    "desk/src/components/kb-credits-portal/**/*.ts",
    "desk/src/pages/kb-credits/**/*.vue",
    "desk/src/pages/kb-credits/**/*.ts",
    "desk/src/components/ticket/TicketCustomerSidebar.vue",
    # copies traduites des composants d'onboarding / aide de frappe-ui
    "desk/src/components/kb-frappe-ui/**/*.vue",
    # écrans agent accueil / notifications, entièrement passés en français
    "desk/src/pages/home/**/*.vue",
    "desk/src/components/notifications/*.vue",
    "desk/src/pages/MobileNotifications.vue",
]


def kb_files() -> list[Path]:
    """Fichiers propres au fork KB (hors fichiers amont passés au codemod)."""
    files: set[Path] = set()
    for pattern in KB_GLOBS:
        files.update(ROOT.glob(pattern))
    return sorted(files)


def target_files() -> list[Path]:
    from codemod_labels import TARGETS  # même dossier

    files: set[Path] = set()
    for pattern in KB_GLOBS:
        files.update(ROOT.glob(pattern))
    for rel in TARGETS:
        p = ROOT / rel
        if p.exists():
            files.add(p)
    return sorted(files)


# ancienne référence générique « #: kb_credits (crédits d'intervention) »
LEGACY_REFS = {"kb_credits", "(crédits", "d'intervention)"}

_CALL = re.compile(r"(?<![\w$.])__\(")


def _read_literal(src: str, i: int) -> tuple[str | None, int]:
    """Lit un littéral chaîne JS commençant à src[i]. Retourne (valeur, fin)."""
    quote = src[i]
    if quote not in "\"'`":
        return None, i
    out = []
    j = i + 1
    while j < len(src):
        c = src[j]
        if c == "\\":
            nxt = src[j + 1]
            out.append({"n": "\n", "t": "\t"}.get(nxt, nxt))
            j += 2
            continue
        if quote == "`" and c == "$" and src[j + 1 : j + 2] == "{":
            return None, j  # gabarit dynamique : non extractible
        if c == quote:
            return "".join(out), j + 1
        out.append(c)
        j += 1
    return None, j


def extract(path: Path) -> list[tuple[str, int]]:
    src = path.read_text(encoding="utf-8")
    found = []
    for m in _CALL.finditer(src):
        j = m.end()
        while j < len(src) and src[j] in " \t\r\n":
            j += 1
        # attribut Vue entre guillemets doubles : __('...') ou __(&quot;...&quot;)
        value, end = _read_literal(src, j)
        if not value:
            continue  # None (non extractible) ou __('') : rien à traduire
        k = end
        while k < len(src) and src[k] in " \t\r\n":
            k += 1
        if k < len(src) and src[k] not in ",)":
            continue  # concaténation : ignorée
        line = src.count("\n", 0, m.start()) + 1
        found.append((value, line))
    return found


def collect() -> dict[str, list[str]]:
    refs: dict[str, list[str]] = defaultdict(list)
    for f in target_files():
        rel = f.relative_to(ROOT).as_posix()
        for msgid, line in extract(f):
            refs[msgid].append(f"{rel}:{line}")
    return refs


def load_po() -> polib.POFile:
    return polib.pofile(str(PO_PATH))


def _block_msgid(block: str) -> str | None:
    """msgid d'un bloc texte du .po (None pour l'en-tête ou un bloc vide)."""
    try:
        po = polib.pofile(block)
    except Exception:
        return None
    entries = [e for e in po]
    return entries[0].msgid if entries else None


def save_po(po: polib.POFile, touched: set[str]) -> None:
    """Réécrit fr.po en ne régénérant QUE les entrées modifiées ou ajoutées ;
    le reste du fichier garde sa mise en forme d'origine (diff minimal, rebase
    facile sur l'amont)."""
    text = PO_PATH.read_text(encoding="utf-8")
    blocks = text.rstrip("\n").split("\n\n")
    by_id = {e.msgid: e for e in po if not e.obsolete}
    seen: set[str] = set()
    out = []
    for i, block in enumerate(blocks):
        mid = _block_msgid(block) if i else None
        if mid is not None:
            seen.add(mid)
        if mid is not None and mid in touched and mid in by_id:
            out.append(by_id[mid].__unicode__(wrapwidth=78).rstrip("\n"))
        else:
            out.append(block)
    for mid in touched:
        if mid not in seen and mid in by_id:
            out.append(by_id[mid].__unicode__(wrapwidth=78).rstrip("\n"))
    PO_PATH.write_text("\n\n".join(out) + "\n", encoding="utf-8")


def placeholders(s: str) -> list[str]:
    return sorted(re.findall(r"\{\d*\}", s))


def cmd_check() -> int:
    refs = collect()
    po = load_po()
    index = {e.msgid: e for e in po if not e.obsolete}
    missing = [m for m in refs if m not in index or not index[m].msgstr.strip()]
    bad_ph = [
        m
        for m in refs
        if m in index and index[m].msgstr and placeholders(m) != placeholders(index[m].msgstr)
    ]
    for m in sorted(missing):
        print(f"MANQUE\t{json.dumps(m, ensure_ascii=False)}\t{refs[m][0]}")
    for m in sorted(bad_ph):
        print(f"PLACEHOLDER\t{json.dumps(m, ensure_ascii=False)}\t{index[m].msgstr!r}")
    print(f"{len(refs)} msgids utilisés, {len(missing)} manquants, {len(bad_ph)} placeholders divergents")
    return 1 if (missing or bad_ph) else 0


def cmd_refs() -> int:
    """Met à jour les références #: fichier:ligne des msgids propres au fork KB
    (retire l'ancienne référence générique « kb_credits (crédits
    d'intervention) »). Les entrées amont ne sont pas modifiées."""
    refs = collect()
    scanned = {f.relative_to(ROOT).as_posix() for f in kb_files()}
    po = load_po()
    changed = 0
    touched: set[str] = set()
    for e in po:
        if e.msgid not in refs:
            continue
        old = list(e.occurrences)
        # entrée amont (références vers d'autres fichiers) : on n'y touche pas,
        # pour garder un diff minimal avec l'amont
        if any(o[0] not in scanned and o[0] not in LEGACY_REFS for o in old):
            continue
        keep = [
            o
            for o in old
            if o[0] not in scanned and o[0] not in LEGACY_REFS
        ]
        new = keep + [tuple(r.rsplit(":", 1)) for r in refs[e.msgid]]
        # dédoublonnage en gardant l'ordre
        seen, dedup = set(), []
        for o in new:
            if o not in seen:
                seen.add(o)
                dedup.append(o)
        if dedup != old:
            e.occurrences = dedup
            changed += 1
            touched.add(e.msgid)
    save_po(po, touched)
    print(f"{changed} entrées mises à jour")
    return 0


def cmd_add(json_path: str) -> int:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    refs = collect()
    po = load_po()
    index = {e.msgid: e for e in po if not e.obsolete}
    added = updated = 0
    touched: set[str] = set()
    for msgid, msgstr in data.items():
        if placeholders(msgid) != placeholders(msgstr):
            print(f"REFUS placeholders: {msgid!r} -> {msgstr!r}", file=sys.stderr)
            continue
        occ = [tuple(r.rsplit(":", 1)) for r in refs.get(msgid, [])]
        if msgid in index:
            e = index[msgid]
            if not e.msgstr.strip():
                e.msgstr = msgstr
                updated += 1
                touched.add(msgid)
            continue
        po.append(polib.POEntry(msgid=msgid, msgstr=msgstr, occurrences=occ))
        touched.add(msgid)
        added += 1
    save_po(po, touched)
    print(f"{added} msgids ajoutés, {updated} traductions complétées")
    return 0


def cmd_stats() -> int:
    po = load_po()
    entries = [e for e in po if not e.obsolete and e.msgid]
    done = [e for e in entries if e.msgstr.strip()]
    print(f"{len(done)}/{len(entries)} = {100 * len(done) / len(entries):.2f} %")
    return 0


def cmd_translations(site: str) -> int:
    """UI-1 : lignes `Translation` (fr) de la base qui contredisent fr.po.

    Une ligne en base prime sur les fichiers .mo : `check` ne la voit pas.
    À lancer depuis `frappe-bench/sites` avec le Python du bench :
        ../env/bin/python ../apps/helpdesk/scripts/kb_i18n.py translations <site>
    Les surcharges volontaires de kb_credits (french_labels.TRADUCTIONS) sont
    ignorées. Code retour 1 s'il reste une contradiction."""
    import frappe  # noqa: PLC0415 — disponible seulement dans le bench

    frappe.init(site=site)
    frappe.connect()
    try:
        try:
            from kb_credits.setup.french_labels import TRADUCTIONS
        except ImportError:
            TRADUCTIONS = {}
        if polib is not None:
            index = {e.msgid: e.msgstr for e in load_po() if not e.obsolete and e.msgstr.strip()}
        else:
            from babel.messages.pofile import read_po

            with open(PO_PATH, "rb") as fh:
                catalog = read_po(fh)
            index = {
                m.id: m.string
                for m in catalog
                if m.id and isinstance(m.id, str) and isinstance(m.string, str) and m.string.strip()
            }
        rows = frappe.db.sql(
            "select name, source_text, translated_text from `tabTranslation` where language = 'fr'",
            as_dict=True,
        )
        bad = [
            r
            for r in rows
            if r.source_text in index
            and index[r.source_text] != r.translated_text
            and TRADUCTIONS.get(r.source_text) != r.translated_text
        ]
        for r in bad:
            print(
                f"CONTREDIT\t{r.name}\t{json.dumps(r.source_text, ensure_ascii=False)}\t"
                f"base={r.translated_text!r}\tfr.po={index[r.source_text]!r}"
            )
        print(f"{len(rows)} traductions en base, {len(bad)} en contradiction avec fr.po")
        return 1 if bad else 0
    finally:
        frappe.destroy()


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "add":
        sys.exit(cmd_add(sys.argv[2]))
    if cmd == "translations":
        sys.exit(cmd_translations(sys.argv[2]))
    sys.exit({"check": cmd_check, "refs": cmd_refs, "stats": cmd_stats}[cmd]())
