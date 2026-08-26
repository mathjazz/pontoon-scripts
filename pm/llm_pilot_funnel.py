"""
LLM pilot adoption funnel (#4394).

Paste the whole file into `./manage.py shell` on the target instance.
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone as dt_timezone

from django.conf import settings

from pontoon.base.models import Translation
from pontoon.uxactionlog.models import UXActionLog


# ---------------------------------------------------------------- parameters

# Pilot Stage 1 Start (6 locales): 2026-08-13
# Pilot Stage 2 Start (26 locales): 2026-08-26
START = datetime(2026, 8, 13, tzinfo=dt_timezone.utc)
END = datetime(2026, 8, 26, tzinfo=dt_timezone.utc)

# Suggestions shown, cache hits, latency and token counts, per locale. This data
# only exists as `llm_suggestion` log lines, so paste it in here. Empty skips the
# first funnel stage, the rates derived from it, and the cost section.
#
# `hits` counts cached responses, which cost nothing but still count as a
# suggestion shown. Latency percentiles cover cache misses only: a hit returns
# in about a millisecond and would otherwise flatter the numbers.
#
#   gcloud logging read '
#       resource.type="k8s_container"
#       AND resource.labels.namespace_name="pontoon-prod"
#       AND textPayload:"llm_suggestion"
#       AND timestamp>="2026-08-13T00:00:00Z"' \
#     --project=moz-fx-webservices-low-prod \
#     --format='value(textPayload)' --limit=200000 --freshness=60d \
#     > llm_suggestion.log
#
# `pontoon-prod` is the Kubernetes namespace on the shared
# `webservices-low-prod` cluster, not a GCP project. --freshness matters:
# `gcloud logging read` defaults to 1 day and silently ignores older entries.
#
# Then aggregate that file into the literals below:
#
#   python3 - llm_suggestion.log <<'PY'
#   import re, sys
#   from collections import defaultdict
#   rows = [dict(re.findall(r'(\w+)=(\S*)', line))
#           for line in open(sys.argv[1]) if 'llm_suggestion' in line]
#   def stats(rs):
#       durs = sorted(int(r['duration_ms']) for r in rs
#                     if r.get('cache_hit') != 'true' and r.get('duration_ms', '').isdigit())
#       tok = lambda k: sum(int(r[k]) for r in rs if r.get(k, '').isdigit())
#       return {'shown': len(rs), 'hits': sum(1 for r in rs if r.get('cache_hit') == 'true'),
#               'p50': durs[len(durs) // 2] if durs else 0,
#               'p95': durs[int(len(durs) * 0.95)] if durs else 0,
#               'prompt_tok': tok('prompt_tokens'), 'completion_tok': tok('completion_tokens')}
#   per, manual = defaultdict(list), []
#   for r in rows:
#       (per[r.get('locale', '?')] if r.get('trigger') == 'auto' else manual).append(r)
#   print('LOG = {')
#   for loc in sorted(per, key=lambda l: -len(per[l])):
#       print(f'    "{loc}": {stats(per[loc])},')
#   print('}')
#   print(f'MANUAL = {stats(manual)}')
#   PY
LOG = {
    "tr": {"shown": 1313, "hits": 430, "p50": 1401, "p95": 3164, "prompt_tok": 501333, "completion_tok": 16363},
    "sl": {"shown": 678, "hits": 108, "p50": 1485, "p95": 3502, "prompt_tok": 332382, "completion_tok": 13780},
    "de": {"shown": 510, "hits": 62, "p50": 1786, "p95": 4691, "prompt_tok": 248790, "completion_tok": 7640},
    "fr": {"shown": 389, "hits": 72, "p50": 1717, "p95": 3619, "prompt_tok": 184950, "completion_tok": 6702},
    "it": {"shown": 263, "hits": 94, "p50": 1855, "p95": 3883, "prompt_tok": 104697, "completion_tok": 6032},
    "es-MX": {"shown": 57, "hits": 6, "p50": 1517, "p95": 3305, "prompt_tok": 29051, "completion_tok": 995},
}

# Same shape, aggregated over every AI dropdown request regardless of locale.
MANUAL = {
    "shown": 64,
    "hits": 3,
    "p50": 2340,
    "p95": 6088,
    "prompt_tok": 36865,
    "completion_tok": 2888,
}

# USD per million tokens for settings.OPENAI_MODEL. Leave as None to report
# token counts without a cost estimate.
PRICE_IN = 4.0
PRICE_OUT = 20.0

SHOWN = {locale: stats["shown"] for locale, stats in LOG.items()}

# Set to None for all locales, which also picks up manual AI dropdown use.
LOCALES = list(settings.OPENAI_AUTO_SUGGESTION_LOCALES) or list(SHOWN) or None

LLM = "openai-chatgpt"

# Compared against the LLM row so the numbers have a baseline.
BASELINE = ["google-translate", "translation-memory"]


# ------------------------------------------------------------ copies (UX log)

COPY_ACTIONS = {
    "Machinery Translation Copied",
    "LLM Translation Copied",
    "LLM Translation Copied via Shortcut",
    "LLM Dropdown Select",
}

copies = defaultdict(Counter)
dropdown = Counter()
dropdown_locales = Counter()

ux = UXActionLog.objects.filter(
    created_at__gte=START,
    created_at__lt=END,
    action_type__in=COPY_ACTIONS,
).values_list("action_type", "data")

for action_type, data in ux.iterator():
    data = data or {}
    locale = data.get("localeCode") or "?"
    if action_type != "Machinery Translation Copied":
        dropdown[action_type] += 1
        if action_type != "LLM Dropdown Select":
            dropdown_locales[locale] += 1
        continue
    if LOCALES is not None and locale not in LOCALES:
        continue
    # `sources` is the comma-joined source list of the copied row, so a
    # composed suggestion contributes to each of its sources.
    for source in (data.get("sources") or "?").split(","):
        copies[locale][f"copied:{source}"] += 1


# --------------------------------------------------- saves (machinery_sources)

saved = Translation.objects.filter(date__gte=START, date__lt=END)
if LOCALES is not None:
    saved = saved.filter(locale__code__in=LOCALES)

saves = defaultdict(lambda: defaultdict(Counter))

rows = saved.exclude(machinery_sources=[]).values_list(
    "locale__code", "machinery_sources", "approved", "rejected", "fuzzy", "user_id"
)
users = defaultdict(set)

for locale, sources, approved, rejected, fuzzy, user_id in rows.iterator():
    for source in sources:
        c = saves[locale][source]
        c["saved"] += 1
        if approved:
            c["approved"] += 1
        elif rejected:
            c["rejected"] += 1
        elif fuzzy:
            c["fuzzy"] += 1
        else:
            c["pending"] += 1
    if LLM in sources and user_id:
        users[locale].add(user_id)


# ------------------------------------------------------------------- report

def pct(n, d):
    return f"{100 * n / d:5.1f}%" if d else "    - "

def kilo(n):
    return f"{n / 1000:.1f}" if n else "-"

out = []

def emit(line=""):
    out.append(line)

def cost(prompt_tok, completion_tok):
    if PRICE_IN is None or PRICE_OUT is None:
        return ""
    usd = (prompt_tok * PRICE_IN + completion_tok * PRICE_OUT) / 1_000_000
    return f"{usd:>8.2f}"

locales = sorted(set(copies) | set(saves) | set(SHOWN))

emit(f"LLM pilot funnel  {START:%Y-%m-%d} → {END:%Y-%m-%d}")
emit(f"locales: {', '.join(LOCALES) if LOCALES else 'all'}")
emit()

# Two halves of one funnel: the left columns come from the `llm_suggestion` log
# lines, the right ones from UXActionLog and Translation.machinery_sources.
header = (
    f"{'locale':<8} {'shown':>7} {'cache':>7} {'p50':>6} {'p95':>6} "
    f"{'in k':>7} {'out k':>7}"
    + (f"{'USD':>8}" if PRICE_IN is not None else "")
    + f" | {'copied':>7} {'copy%':>7} {'saved':>6} {'save%':>7} "
    f"{'appr':>5} {'rej':>4} {'pend':>5} {'appr%':>7} {'users':>6}"
)
emit(header)
emit("-" * len(header))

def row(label, log, copied, s, user_count):
    shown = log.get("shown", 0)
    return (
        f"{label:<8} {shown or '-':>7} {pct(log.get('hits', 0), shown):>7} "
        f"{log.get('p50', 0) or '-':>6} {log.get('p95', 0) or '-':>6} "
        f"{kilo(log.get('prompt_tok', 0)):>7} {kilo(log.get('completion_tok', 0)):>7}"
        + cost(log.get("prompt_tok", 0), log.get("completion_tok", 0))
        + f" | {copied:>7} {pct(copied, shown):>7} {s['saved']:>6} "
        f"{pct(s['saved'], copied):>7} {s['approved']:>5} {s['rejected']:>4} "
        f"{s['pending'] + s['fuzzy']:>5} {pct(s['approved'], s['saved']):>7} "
        f"{user_count:>6}"
    )

totals = Counter()
log_totals = Counter()
for locale in locales:
    log = LOG.get(locale, {})
    copied = copies[locale][f"copied:{LLM}"]
    s = saves[locale][LLM]
    emit(row(locale, log, copied, s, len(users[locale])))
    log_totals.update(log)
    totals.update(
        {
            "copied": copied,
            "saved": s["saved"],
            "approved": s["approved"],
            "rejected": s["rejected"],
            "pending": s["pending"] + s["fuzzy"],
            "fuzzy": 0,
        }
    )

if LOG:
    log_totals["p50"] = min(s["p50"] for s in LOG.values())
    log_totals["p95"] = max(s["p95"] for s in LOG.values())

emit("-" * len(header))
emit(
    row(
        "total",
        log_totals,
        totals["copied"],
        totals,
        len(set().union(*users.values())) if users else 0,
    )
)
emit()
emit(
    "cache/p50/p95/in k/out k from llm_suggestion log lines; percentiles cover "
    "cache misses only and span locales on the total row"
)

# The dropdown path is a different funnel: the suggestion replaces the Google
# Translate row in place, so a copy of it is logged as an LLM action rather
# than as a Machinery copy, and a save is attributed to `openai-chatgpt` all
# the same. Reported separately so it does not inflate the automatic numbers,
# and across all locales, since the dropdown is not limited to the pilot ones.
emit()
emit("AI dropdown (manual trigger, all locales)")
if MANUAL:
    emit(
        f"  {'requested':<38} {MANUAL['shown']:>8}   "
        f"cache {pct(MANUAL['hits'], MANUAL['shown']).strip()}, "
        f"p50 {MANUAL['p50']} ms, p95 {MANUAL['p95']} ms, "
        f"{kilo(MANUAL['prompt_tok'])}k in / {kilo(MANUAL['completion_tok'])}k out"
        + (
            f", {cost(MANUAL['prompt_tok'], MANUAL['completion_tok']).strip()} USD"
            if PRICE_IN is not None
            else ""
        )
    )


for action in sorted(COPY_ACTIONS - {"Machinery Translation Copied"}):
    emit(f"  {action:<38} {dropdown[action]:>8}")

if dropdown_locales:
    emit(
        "  copied in: "
        + ", ".join(f"{loc} {n}" for loc, n in dropdown_locales.most_common())
    )

emit()
emit("Baseline: saves by Machinery source")
emit(f"  {'source':<24} {'saved':>8} {'approved':>9} {'appr%':>7}")
for source in [LLM] + BASELINE:
    saved_n = sum(saves[locale][source]["saved"] for locale in locales)
    appr_n = sum(saves[locale][source]["approved"] for locale in locales)
    emit(f"  {source:<24} {saved_n:>8} {appr_n:>9} {pct(appr_n, saved_n):>7}")

emit()
emit("Baseline: copies by Machinery source")
sources = Counter()
for locale in locales:
    for key, count in copies[locale].items():
        if key.startswith("copied:"):
            sources[key[len("copied:") :]] += count

for source, count in sources.most_common():
    emit(f"  {source:<24} {count:>8}")

print("\n" + "\n".join(out) + "\n")
