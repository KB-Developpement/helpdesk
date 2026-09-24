#!/usr/bin/env python3
"""Codemod i18n du fork KB du Helpdesk : entoure de __() les libellés anglais
en dur de l'interface (agent + portail client) pour qu'ils passent par
helpdesk/locale/fr.po.

Idempotent : un libellé déjà entouré n'est plus reconnu par les motifs, on
peut donc relancer le script après chaque rebase sur l'amont.

    python3 scripts/codemod_labels.py            # applique
    python3 scripts/codemod_labels.py --check    # n'écrit rien, code retour 1 s'il reste du travail
    python3 scripts/codemod_labels.py --scan F…  # liste les candidats d'autres fichiers (sans écrire)

Principe de prudence : on ne traduit QUE l'affichage. Toute valeur envoyée au
serveur ou comparée dans le code (statut label_agent, titre d'onglet comparé,
libellé de colonne testé…) reste en anglais et est traduite au point
d'affichage (« sink ») par une règle explicite.

Passes génériques (sur la section <template> des fichiers ciblés) :
  G1  label="Text" / placeholder="Text" / title="Text"   ->  :label="__('Text')"
  G2  texte brut entre balises  >Text<                    ->  >{{ __("Text") }}<
  G3  :label="'Text'" (littéral seul lié)                 ->  :label="__('Text')"
Passes script (uniquement pour les clés déclarées « affichage » du fichier) :
  S1  label: "Text"                                       ->  label: __("Text")
  S2  label: `Text ${expr} text`                          ->  label: __("Text {0} text", expr)
Puis les remplacements explicites (REPLACE) propres à chaque fichier.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = "desk/src/"

# fichier -> options. script_keys : clés d'objets JS dont la valeur littérale
# n'est QUE de l'affichage dans ce fichier (vérifié à la main).
TARGETS: dict[str, dict] = {
    # --- fil d'activité du ticket (agent) ---
    "components/ticket-agent/TicketActivityPanel.vue": {"script_keys": ["label"]},
    "pages/ticket/MobileTicketAgent.vue": {"script_keys": []},
    "components/ticket/TicketAgentActivities.vue": {},
    "components/ticket/ActivityHeader.vue": {},
    "components/HistoryBox.vue": {},
    "components/CommunicationArea.vue": {},
    "components/EmailEditor.vue": {},
    "components/CommentTextEditor.vue": {},
    "components/ticket/TicketFeedback.vue": {},
    # --- en-tête / SLA / panneaux latéraux agent ---
    "components/ticket-agent/TicketHeader.vue": {},
    "components/ticket-agent/TicketSLA.vue": {"script_keys": ["label"]},
    "components/ticket/TicketAgentDetails.vue": {"script_keys": ["label"]},
    "components/ticket-agent/TicketDetailsTab.vue": {},
    "components/ticket-agent/TicketContactTab.vue": {},
    # --- portail client : ticket ---
    "components/ticket/TicketCustomerSidebar.vue": {"script_keys": ["label"]},
    "pages/ticket/TicketCustomerTemplateFields.vue": {"script_keys": ["title"]},
    # --- listes ---
    "pages/ticket/Tickets.vue": {"script_keys": ["title"]},
    "components/ListViewBuilder.vue": {},
    "components/EmptyState.vue": {},
    # toutes les options { label: "…", value: "…" } : le label n'est qu'affiché
    "components/view-controls/Filter.vue": {"script_keys": ["label"]},
    "components/view-controls/SortBy.vue": {},
    "components/view-controls/ColumnSettings.vue": {},
    "components/view-controls/Reload.vue": {},
    "components/view-controls/QuickFilterField.vue": {},
    "pages/desk/customer/Customers.vue": {"script_keys": ["title"]},
    "pages/desk/contact/Contacts.vue": {"script_keys": ["title"]},
    # --- base de connaissances (portail) ---
    "pages/knowledge-base/KnowledgeBaseCustomer.vue": {"script_keys": ["title"]},
    "pages/knowledge-base/Articles.vue": {"script_keys": ["label"]},
    # --- tableau de bord agent ---
    "pages/dashboard/Dashboard.vue": {"script_keys": ["label", "title", "message"]},
    # --- composants partagés (passes génériques du <template> seulement) ---
    "pages/ticket/TicketConversation.vue": {},
    "pages/knowledge-base/Article.vue": {},
    "components/SearchArticles.vue": {},
    "components/Autocomplete.vue": {},
    "components/Apps.vue": {},
    "components/CommentBox.vue": {},
    "components/ConfirmDialog.vue": {},
    "components/IconPicker.vue": {},
    "components/SearchComplete.vue": {},
    "components/SearchMultiSelect.vue": {},
    "components/TextEditor.vue": {},
    "components/ViewBreadcrumbs.vue": {},
    "components/ViewModal.vue": {},
    "components/knowledge-base/ArticleFeedback.vue": {},
    "components/knowledge-base/CategoryModal.vue": {},
    "components/knowledge-base/MergeCategoryModal.vue": {},
    "components/knowledge-base/MoveToCategoryModal.vue": {},
    "components/layouts/MobileSidebar.vue": {},
    "components/layouts/Sidebar.vue": {},
    "components/ticket/TicketMergeModal.vue": {},
    "components/ticket/TicketSplitModal.vue": {},
    # --- durées affichées (échéances SLA des listes et fiches) ---
    "utils.ts": {},
}
TARGETS = {SRC + k: v for k, v in TARGETS.items()}

# Remplacements explicites (ancien, nouveau). Chaque « nouveau » ne doit pas
# recontenir l'« ancien » (idempotence). Dans un attribut de <template> entre
# guillemets doubles, n'utiliser QUE des guillemets simples dans le JS.
REPLACE: dict[str, list[tuple[str, str]]] = {
    # Le titre d'onglet arrive traduit (TicketActivityPanel) : on compare au
    # libellé traduit, et les textes vides passent par __().
    "components/ticket/TicketAgentActivities.vue": [
        ('props.title === "Emails") return "No email communications"',
         'props.title === __("Emails")) return __("No email communications")'),
        ('props.title === "Comments") return "No comments found"',
         'props.title === __("Comments")) return __("No comments found")'),
        ('props.title === "Calls") return "No calls made"',
         'props.title === __("Calls")) return __("No calls made")'),
        ('return "No activity found";', 'return __("No activity found");'),
        ('props.title == "Emails"', 'props.title == __("Emails")'),
        ('props.title == "Comments"', 'props.title == __("Comments")'),
        ('props.title == "Calls"', 'props.title == __("Calls")'),
    ],
    "components/ticket/ActivityHeader.vue": [
        ("v-if=\"title == 'Calls'\"", "v-if=\"title == __('Calls')\""),
    ],
    "pages/ticket/MobileTicketAgent.vue": [
        ('label: "Activity",', 'label: __("Activity"),'),
        ('label: "Emails",', 'label: __("Emails"),'),
        ('label: "Comments",', 'label: __("Comments"),'),
        ('label: "Calls",', 'label: __("Calls"),'),
        ('label: "Details",', 'label: __("Details"),'),
    ],
    # « viewed this » sert de clé de regroupement : traduit à l'affichage.
    "components/HistoryBox.vue": [
        ('<span>{{ `${show_others ? "Hide " : "Show "}` }}</span>\n'
         '        <span>+{{ relatedActivities.length }} </span>\n'
         '        <span>changes from </span>',
         '<span>{{\n'
         '          show_others\n'
         '            ? __("Hide +{0} changes from", String(relatedActivities.length))\n'
         '            : __("Show +{0} changes from", String(relatedActivities.length))\n'
         '        }}</span>'),
        ("<span> {{ content }}</span>", "<span> {{ __(content) }}</span>"),
        ("<span> {{ relatedActivity.content }}</span>",
         "<span> {{ __(relatedActivity.content) }}</span>"),
    ],
    "components/CommunicationArea.vue": [
        ("isMobileView ? 'Send' : isMac ? 'Send (⌘ + ⏎)' : 'Send (Ctrl + ⏎)'",
         "isMobileView ? __('Send') : isMac ? __('Send (⌘ + ⏎)') : __('Send (Ctrl + ⏎)')"),
        ("? 'Comment'\n                : isMac\n                ? 'Comment (⌘ + ⏎)'\n                : 'Comment (Ctrl + ⏎)'",
         "? __('Comment')\n                : isMac\n                ? __('Comment (⌘ + ⏎)')\n                : __('Comment (Ctrl + ⏎)')"),
    ],
    # Statut agent : la valeur reste label_agent (envoyée au serveur),
    # seul le libellé affiché est traduit.
    "components/ticket-agent/TicketHeader.vue": [
        ('<Button :label="ticket.doc.status" ref="statusRef">',
         '<Button :label="__(ticket.doc.status)" ref="statusRef">'),
        ("    label: o.label_agent,\n    value: o.label_agent,",
         "    label: __(o.label_agent),\n    value: o.label_agent,"),
    ],
    "components/ticket-agent/TicketDetailsTab.vue": [
        ("                      {{ t.status }}", "                      {{ __(t.status) }}"),
        # libellés des champs cœur (Ticket Type, Priority, Customer, Team…)
        ('              :label="field.label"\n              :placeholder="field.placeholder"',
         '              :label="__(field.label)"\n              :placeholder="field.placeholder"'),
        ("      `Enter ${fieldMeta?.label || fieldTemplate.fieldname}`,",
         '      __("Enter {0}", __(fieldMeta?.label || fieldTemplate.fieldname)),'),
    ],
    "components/ticket-agent/TicketContactTab.vue": [
        ("                  {{ ticket.status }}", "                  {{ __(ticket.status) }}"),
    ],
    "pages/ticket/Tickets.vue": [
        ('          : status?.["label_agent"];', '          : __(status?.["label_agent"]);'),
    ],
    # data.title sert aussi de clé (=== 'Resolution') : traduit à l'affichage.
    "components/ticket/TicketCustomerSidebar.vue": [
        ('<div class="w-[126px] text-ink-gray-5 text-sm">{{ data.title }}</div>',
         '<div class="w-[126px] text-ink-gray-5 text-sm">\n          {{ __(data.title) }}\n        </div>'),
        ('<span class="w-[126px] text-sm text-ink-gray-5">{{ field.label }}</span>',
         '<span class="w-[126px] text-sm text-ink-gray-5">{{\n          __(field.label)\n        }}</span>'),
    ],
    "pages/ticket/TicketCustomerTemplateFields.vue": [
        ("<Badge :label=\"data.label\"", "<Badge :label=\"__(data.label)\""),
        (":label=\"data.label\"\n", ":label=\"__(data.label)\"\n"),
    ],
    "components/ticket-agent/TicketSLA.vue": [
        ("`Ticket #${ticket.doc.name} copied to clipboard`",
         "__('Ticket #{0} copied to clipboard', ticket.doc.name)"),
        ("label: `On Hold`,", 'label: __("On Hold"),'),
        ("return `${years}y ${months}mo`;", 'return __("{0}y {1}mo", String(years), String(months));'),
        ("return `${months}mo ${days}d`;", 'return __("{0}mo {1}d", String(months), String(days));'),
        ("return `${days}d ${hours}h`;", 'return __("{0}d {1}h", String(days), String(hours));'),
    ],
    "components/ticket/TicketAgentDetails.vue": [
        # les libellés de sections sont traduits dans le script (clé label)
        ('value: props.ticket.via_customer_portal ? "Portal" : "Mail",',
         'value: props.ticket.via_customer_portal ? __("Portal") : __("Mail"),'),
    ],
    # Les libellés de colonnes viennent du serveur en anglais : traduits dans
    # l'en-tête seulement (column.label reste comparé à "Status" plus bas).
    "components/ListViewBuilder.vue": [
        # listes de champs pour Filtrer / Trier : libellé traduit, valeur =
        # fieldname inchangée
        ("        label: field.label,\n        value: field.fieldname,\n        ...field,\n",
         "        value: field.fieldname,\n        ...field,\n        label: __(field.label),\n"),
        ('  url: "helpdesk.api.doc.sort_options",\n  auto: !options.value.hideViewControls,\n  params: {',
         '  url: "helpdesk.api.doc.sort_options",\n  auto: !options.value.hideViewControls,\n'
         '  transform: (data) =>\n    (data || []).map((o) => ({ ...o, label: __(o.label) })),\n  params: {'),
        ('        @columnWidthUpdated="handleColumnResize"\n      />',
         '        @columnWidthUpdated="handleColumnResize"\n      >\n'
         '        <div class="truncate">{{ __(column.label) }}</div>\n'
         '      </ListHeaderItem>'),
    ],
    "components/view-controls/Filter.vue": [
        ("        label: o,\n        value: o,", "        label: __(o),\n        value: o,"),
    ],
    # libellés des filtres rapides (champs du doctype, en anglais côté serveur)
    "components/view-controls/QuickFilterField.vue": [
        (':label="filter.label"', ':label="__(filter.label)"'),
        (':placeholder="filter.label"', ':placeholder="__(filter.label)"'),
        (':options="filter.options"',
         ':options="(filter.options || []).map((o) => ({ ...o, label: __(o.label) }))"'),
    ],
    "components/view-controls/ColumnSettings.vue": [
        ("<div>{{ element.label }}</div>", "<div>{{ __(element.label) }}</div>"),
    ],
    "components/EmptyState.vue": [],
    "utils.ts": [
        ('${years === 1 ? "year" : "years"}', '${years === 1 ? __("year") : __("years")}'),
        ('${months === 1 ? "month" : "months"}', '${months === 1 ? __("month") : __("months")}'),
        ('${days === 1 ? "day" : "days"}', '${days === 1 ? __("day") : __("days")}'),
        ("formattedTime += `${days}d `;", 'formattedTime += __("{0}d", String(days)) + " ";'),
    ],
    "pages/knowledge-base/Articles.vue": [
        ('title: `${categoryTitle?.value}` + " - " + "Knowledge Base",',
         'title: `${categoryTitle?.value}` + " - " + __("Knowledge Base"),'),
    ],
    "pages/dashboard/Dashboard.vue": [
        ("title: `No ${(chart?.title).toLowerCase()} available.`,",
         "title: __('No {0} available.', __(chart?.title).toLowerCase()),"),
    ],
}
REPLACE = {SRC + k: v for k, v in REPLACE.items()}

TRANSLATION_IMPORT = 'import { __ } from "@/translation";'

# ---------------------------------------------------------------- helpers
WORDY = re.compile(r"[A-Za-z]{2,}")
TEXT_OK = re.compile(r"^[A-Za-z][A-Za-z0-9 ,.;:!?'’()/+\-…—%#]*$")
BAD_TEXT = ("&&", "||", "==", "=>", "&", "{", "}", "http", "@")
SKIP_TEXT = {"Esc", "OK", "SLA", "ID", "px", "rem"}


def _is_label_text(s: str) -> bool:
    s = " ".join(s.split())
    if not s or s in SKIP_TEXT or any(b in s for b in BAD_TEXT):
        return False
    return bool(TEXT_OK.match(s)) and bool(WORDY.search(s))


def _template_span(src: str) -> tuple[int, int] | None:
    start = src.find("<template")
    if start < 0:
        return None
    script = src.find("<script")
    end_limit = script if script > start else len(src)
    end = src.rfind("</template>", start, end_limit)
    if end < 0:
        return None
    return start, end


def _js_single(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _js_double(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


# G1 : attribut statique
ATTR_STATIC = re.compile(
    r'(?<=[\s])(label|placeholder|title)="([^"{}<>]*)"(?=[\s/>])'
)
# G3 : attribut lié à un littéral seul
ATTR_BOUND = re.compile(
    r"""(?<=[\s]):(label|placeholder|title|text)="'([^'"\\{}]*)'"(?=[\s/>])"""
)
# G2 : texte brut
TEXT_NODE = re.compile(r">([^<>]+)<")


def transform_template(tpl: str) -> str:
    def g1(m):
        attr, val = m.group(1), m.group(2)
        if not _is_label_text(val):
            return m.group(0)
        return f":{attr}=\"__('{_js_single(' '.join(val.split()))}')\""

    def g3(m):
        attr, val = m.group(1), m.group(2)
        if not _is_label_text(val):
            return m.group(0)
        return f":{attr}=\"__('{_js_single(val)}')\""

    def g2(m):
        raw = m.group(1)
        if not raw.strip() or not _is_label_text(raw):
            return m.group(0)
        lead = raw[: len(raw) - len(raw.lstrip())]
        trail = raw[len(raw.rstrip()) :]
        text = " ".join(raw.split())
        return f'>{lead}{{{{ __("{_js_double(text)}") }}}}{trail}<'

    # les commentaires HTML sont laissés tels quels
    chunks = re.split(r"(<!--.*?-->)", tpl, flags=re.S)
    for n in range(0, len(chunks), 2):
        c = ATTR_STATIC.sub(g1, chunks[n])
        c = ATTR_BOUND.sub(g3, c)
        chunks[n] = TEXT_NODE.sub(g2, c)
    return "".join(chunks)


def _scan_template_literal(src: str, i: int) -> tuple[list[str], list[str], int] | None:
    """src[i] == '`'. Retourne (morceaux texte, expressions, fin)."""
    parts, exprs, buf = [], [], []
    j = i + 1
    while j < len(src):
        c = src[j]
        if c == "\\":
            buf.append(src[j : j + 2])
            j += 2
            continue
        if c == "`":
            parts.append("".join(buf))
            return parts, exprs, j + 1
        if c == "$" and src[j + 1 : j + 2] == "{":
            parts.append("".join(buf))
            buf = []
            depth, k = 1, j + 2
            while k < len(src) and depth:
                if src[k] == "{":
                    depth += 1
                elif src[k] == "}":
                    depth -= 1
                elif src[k] == "`":
                    return None  # gabarit imbriqué : on s'abstient
                k += 1
            exprs.append(src[j + 2 : k - 1])
            j = k
            continue
        buf.append(c)
        j += 1
    return None


def transform_script(src: str, keys: list[str]) -> str:
    if not keys:
        return src
    key_alt = "|".join(map(re.escape, keys))
    # S1 : clé: "Texte"
    s1 = re.compile(r'(?<![\w.$])(' + key_alt + r')(\s*:\s*)"([^"\\\n]*)"')

    def r1(m):
        if not _is_label_text(m.group(3)):
            return m.group(0)
        return f'{m.group(1)}{m.group(2)}__("{m.group(3)}")'

    src = s1.sub(r1, src)
    # S2 : clé: `Texte ${expr}`
    s2 = re.compile(r"(?<![\w.$])(" + key_alt + r")(\s*:\s*)`")
    out, pos = [], 0
    for m in s2.finditer(src):
        if m.start() < pos:
            continue
        tick = m.end() - 1
        scanned = _scan_template_literal(src, tick)
        if not scanned:
            continue
        parts, exprs, end = scanned
        if not exprs:
            text = parts[0]
            if not _is_label_text(text):
                continue
            repl = f'{m.group(1)}{m.group(2)}__("{_js_double(text)}")'
        else:
            msgid = "".join(p + (f"{{{n}}}" if n < len(exprs) else "") for n, p in enumerate(parts))
            if not WORDY.search("".join(parts)) or not _is_label_text(
                re.sub(r"\{\d\}", "x", msgid).strip() or "x"
            ):
                continue
            args = ", ".join(e.strip() for e in exprs)
            repl = f'{m.group(1)}{m.group(2)}__("{_js_double(msgid)}", {args})'
        out.append(src[pos : m.start()])
        out.append(repl)
        pos = end
    out.append(src[pos:])
    return "".join(out)


def ensure_import(src: str) -> str:
    script = src.find("<script")
    if script < 0 or "@/translation" in src[script:]:
        return src
    body = src[script:]
    if not re.search(r"(?<![\w$.])__\(", body):
        return src
    tag_end = src.find(">", script) + 1
    return src[:tag_end] + "\n" + TRANSLATION_IMPORT + src[tag_end:]


def process(path: Path, opts: dict, replaces: list[tuple[str, str]], text: str | None = None) -> str:
    src = path.read_text(encoding="utf-8") if text is None else text
    new = src
    for old, rep in replaces:
        new = new.replace(old, rep)
    span = _template_span(new)
    if span:
        a, b = span
        new = new[:a] + transform_template(new[a:b]) + new[b:]
    script = new.find("<script")
    if script >= 0:
        new = new[:script] + transform_script(new[script:], opts.get("script_keys", []))
    elif path.suffix in (".ts", ".js"):
        new = transform_script(new, opts.get("script_keys", []))
    return ensure_import(new)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    if "--scan" in argv:
        files = [Path(a) for a in argv[argv.index("--scan") + 1 :]]
        for f in files:
            src = f.read_text(encoding="utf-8")
            new = process(f, {}, [])
            if new != src:
                n = sum(1 for x, y in zip(src.splitlines(), new.splitlines()) if x != y)
                print(f"{f}\t~{n} lignes")
        return 0
    touched = []
    for rel, opts in TARGETS.items():
        path = ROOT / rel
        if not path.exists():
            print(f"absent (amont modifié ?) : {rel}", file=sys.stderr)
            continue
        src = path.read_text(encoding="utf-8")
        new = process(path, opts, REPLACE.get(rel, []))
        # contrôle : un second passage ne doit rien changer (idempotence)
        if process(path, opts, REPLACE.get(rel, []), new) != new:
            print(f"NON IDEMPOTENT : {rel}", file=sys.stderr)
            return 2
        if new != src:
            touched.append(rel)
            if not check:
                path.write_text(new, encoding="utf-8")
    for rel in touched:
        print(("à modifier : " if check else "modifié : ") + rel)
    print(f"{len(touched)} fichier(s) {'à modifier' if check else 'modifié(s)'}")
    return 1 if (check and touched) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
