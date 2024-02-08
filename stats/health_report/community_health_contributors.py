"""
Retrieve a list of active contributors for given locales, timeframe and roles.

Output is formatted as CSV with the following columns:
* Locale
* Profile URL
* Role
* Date Joined
* Last Login (date)
* Last Login (months ago)
* Latest Activity
* Reviews Performed
* Approved Translations
* Rejected Translations
* Pending Suggestions

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
LOCALES = [
    # Top 15 (+es-CL)
    "cs",
    "de",
    "es-AR",
    "es-CL",
    "es-ES",
    "es-MX",
    "fr",
    "hu",
    "id",
    "it",
    "ja",
    "nl",
    "pl",
    "pt-BR",
    "ru",
    "zh-CN",
    # Top 25
    "tr",
    "el",
    "zh-TW",
    "fi",
    "pt-PT",
    "sv-SE",
    "vi",
    "sk",
    "ar",
]
EXCLUDED_USERS = ["Imported", "google-translate", "translation-memory"]
START_DATE = "01/01/2023"  # DD/MM/YYYY
END_DATE = "31/12/2023"  # DD/MM/YYYY
LOCALES.sort()

# Script
from __future__ import division
from datetime import datetime
from django.conf import settings
from django.contrib.humanize.templatetags import humanize
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.timezone import get_current_timezone
from pontoon.actionlog.models import ActionLog
from pontoon.base.models import Locale
from pontoon.contributors.utils import users_with_translations_counts
from urllib.parse import urljoin

tz = get_current_timezone()
end_date = tz.localize(datetime.strptime(END_DATE, "%d/%m/%Y"))
start_date = tz.localize(datetime.strptime(START_DATE, "%d/%m/%Y"))


def last_login(user):
    if not user.last_login:
        return "Never logged in"
    else:
        return user.last_login.date()


def time_since_login(user):
    if not user.last_login:
        return "Never logged in"
    return humanize.naturaltime(user.last_login)


def get_profile(username):
    return urljoin(
        settings.SITE_URL,
        reverse("pontoon.contributors.contributor.username", args=[username]),
    )


locales = Locale.objects.all().order_by("code")
if LOCALES:
    locales = locales.filter(code__in=LOCALES)

output = [
    f"Locales: {','.join(locales.values_list('code', flat=True))}",
    f"Start date: {start_date.strftime('%Y-%m-%d')}",
    f"End date: {end_date.strftime('%Y-%m-%d')}\n",
]
output.append(
    "Locale,Profile URL,Role,Date Joined,Last Login (date),Last Login (time ago),Latest Activity,Reviews Performed,Approved Translations,Rejected Translations,Pending Suggestions"
)

for locale in locales:
    contributors = users_with_translations_counts(
        start_date, Q(locale=locale, date__lte=end_date), None
    )
    actions = (
        ActionLog.objects.filter(
            translation__locale=locale,
            created_at__gte=start_date,
            created_at__lte=end_date,
            performed_by__in=contributors,
            action_type__in=[
                ActionLog.ActionType.TRANSLATION_APPROVED,
                ActionLog.ActionType.TRANSLATION_REJECTED,
            ],
        )
        # Group actions by their author (performed_by) and assign counts
        .values("performed_by")
        .annotate(count=Count("id"))
    )
    reviews_performed = {action["performed_by"]: action["count"] for action in actions}
    for contributor in contributors:
        role = contributor.locale_role(locale)
        # Ignore admins
        if role == "Admin":
            continue
        # Ignore imported strings and pretranslations
        if contributor.username in EXCLUDED_USERS:
            continue
        output.append(
            f"{locale.code},{get_profile(contributor.username)},{role},"
            f'{contributor.date_joined.date()},{last_login(contributor)},"{time_since_login(contributor)}",'
            f"{contributor.latest_action.created_at.strftime('%Y-%m-%d')},{reviews_performed.get(contributor.pk, 0)},"
            f"{contributor.translations_approved_count},{contributor.translations_rejected_count},{contributor.translations_unapproved_count}"
        )

print("\n".join(output))
