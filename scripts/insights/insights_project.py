"""
Insights for given project.
"""

from pontoon.insights.models import ProjectInsightsSnapshot

PROJECT = "mozilla-vpn-client"

for p in ProjectInsightsSnapshot.objects.filter(project__slug=PROJECT).order_by(
    "created_at"
):
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
