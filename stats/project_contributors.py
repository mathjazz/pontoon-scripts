"""
Retrieve a list of active contributors for given project and timeframe.

Output is formatted as CSV with the following columns:
* project
* date_joined
* profile_url
* total_submission_count
* approved_count
* rejected_count
* unreviewed_count
* approved_rejected_ratio

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
# Use empty list for all projects
PROJECTS = [
    "firefox",
]
START_DATE = (2022, 1, 1)
END_DATE = (2022, 12, 31)


# Script
from __future__ import division
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from pontoon.base.models import Project, Translation
from pontoon.contributors.utils import users_with_translations_counts

projects = Project.objects.all()
if PROJECTS:
    projects = projects.filter(slug__in=PROJECTS)

start_date = timezone.datetime(*START_DATE, tzinfo=timezone.utc)
end_date = timezone.datetime(*END_DATE, tzinfo=timezone.utc)


def get_profile(username):
    from urllib.parse import urljoin
    return urljoin(
        settings.SITE_URL,
        reverse("pontoon.contributors.contributor.username", args=[username]),
    )


def get_ratio(approved, rejected):
    try:
        return format(approved / (approved + rejected), ".2f")
    except ZeroDivisionError:
        return "-1"


def get_latest_activity(user):
    translations = Translation.objects.filter(Q(user=user) | Q(approved_user=user))
    if not translations.exists():
        return "No activity yet"
    translated = translations.latest("date").date
    approved = translations.latest("approved_date").approved_date
    activities = []
    if translated:
        activities.append(translated)
    if approved:
        activities.append(approved)
    activities.sort()
    return activities[-1].date() if len(activities) > 0 else None


output = []
output.append(
    "Project,Date Joined,Latest Activity,Profile URL,Translations,Approved,Rejected,Pending,Ratio"
)
for project in projects:
    contributors = users_with_translations_counts(
        start_date,
        Q(entity__resource__project=project, date__lte=end_date),
        None,
    )
    for contributor in contributors:
        # Ignore "imported" strings
        if contributor.username == "Imported":
            continue
        output.append(
            "{},{},{},{},{},{},{},{},{}".format(
                project.slug,
                contributor.date_joined.date(),
                get_latest_activity(contributor),
                get_profile(contributor.username),
                contributor.translations_count,
                contributor.translations_approved_count,
                contributor.translations_rejected_count,
                contributor.translations_unapproved_count,
                get_ratio(
                    contributor.translations_approved_count,
                    contributor.translations_rejected_count,
                ),
            )
        )

print("\n".join(output))
