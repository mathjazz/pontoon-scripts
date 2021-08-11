"""
Insights for given project and locale.
"""

from pontoon.insights.models import ProjectLocaleInsightsSnapshot

PROJECT = "mozilla-vpn-client"
LOCALE = "de"

for p in ProjectLocaleInsightsSnapshot.objects.filter(
    project_locale__project__slug=PROJECT, project_locale__locale__code=LOCALE
).order_by("created_at"):
    print(
        "{}, {}, {}, {}, {}, {}, {}, {}".format(
            p.created_at,
            p.completion,
            p.total_strings,
            p.approved_strings,
            p.fuzzy_strings,
            p.strings_with_errors,
            p.strings_with_warnings,
            p.unreviewed_strings,
        )
    )
