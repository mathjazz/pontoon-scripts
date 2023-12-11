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
* Total Reviews
* Approved
* Rejected
* Pending

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
LOCALES = [
    "cs", "de", "es-AR", "es-CL", "es-ES", "es-MX", "fr", "hu", "id", "it",
    "ja", "nl", "pl", "pt-BR", "ru", "zh-CN",
]
EXCLUDED_USERS = ["Imported", "google-translate", "translation-memory"]
END_DATE = "10/12/2023"  # DD/MM/YYYY
DAYS_INTERVAL = 365

# Script
from __future__ import division
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags import humanize
from django.db.models import F, Q
from django.urls import reverse
from django.utils.timezone import get_current_timezone
from pontoon.base.models import Locale, Translation
from pontoon.contributors.utils import users_with_translations_counts
from urllib.parse import urljoin

tz = get_current_timezone()
end_date = tz.localize(datetime.strptime(END_DATE, "%d/%m/%Y"))
start_date = end_date - relativedelta(days=DAYS_INTERVAL)


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


def get_contribution_data(locale):
    users = {}
    # Translations submitted in Pontoon for given locale and timeframe
    translations = Translation.objects.filter(
        locale=locale,
        date__gte=start_date,
        date__lte=end_date,
    )
    # Above translations that have been approved, but not self-approved
    approved = translations.filter(approved_user__isnull=False).exclude(
        user=F("approved_user")
    )
    approved_users = User.objects.filter(
        pk__in=approved.values_list("approved_user", flat=True).distinct()
    )
    for user in approved_users:
        users[user.username] = {
            "approvals": approved.filter(approved_user=user).count(),
            "rejections": 0,
        }
    # Above translations that have been rejected, but not self-rejected
    rejected = translations.filter(rejected_user__isnull=False).exclude(
        user=F("rejected_user")
    )
    rejected_users = User.objects.filter(
        pk__in=rejected.values_list("rejected_user", flat=True).distinct()
    )
    for user in rejected_users:
        if user.username in users:
            users[user.username]["rejections"] = rejected.filter(
                rejected_user=user
            ).count()
        else:
            users[user.email] = {
                "approvals": 0,
                "rejections": rejected.filter(rejected_user=user).count(),
            }
    for user, user_data in users.items():
        user_data["total"] = user_data["approvals"] + user_data["rejections"]
    return users


locales = Locale.objects.all().order_by("code")
if LOCALES:
    locales = locales.filter(code__in=LOCALES)

output = [
    f"Locales: {','.join(locales.values_list('code', flat=True))}",
    f"Start date: {start_date.strftime('%Y-%m-%d')}",
    f"End date: {end_date.strftime('%Y-%m-%d')}\n",
]
output.append(
    "Locale,Profile URL,Role,Date Joined,Last Login (date),Last Login (months ago),Latest Activity,Reviews,Approved,Rejected,Pending"
)
for locale in locales:
    contributors = users_with_translations_counts(
        start_date, Q(locale=locale, date__lte=end_date), None
    )
    contribution_data = get_contribution_data(locale)
    for contributor in contributors:
        role = contributor.locale_role(locale)
        # Ignore admins
        if role == "Admin":
            continue
        # Ignore imported strings and pretranslations
        if contributor.username in EXCLUDED_USERS:
            continue
        output.append(
            "{},{},{},{},{},{},{},{},{},{},{}".format(
                locale.code,
                get_profile(contributor.username),
                role,
                contributor.date_joined.date(),
                last_login(contributor),
                time_since_login(contributor),
                contributor.latest_action.created_at.strftime('%Y-%m-%d'),
                contribution_data.get(contributor.username, {}).get("total", 0),
                contributor.translations_approved_count,
                contributor.translations_rejected_count,
                contributor.translations_unapproved_count,
            )
        )

print("\n".join(output))
