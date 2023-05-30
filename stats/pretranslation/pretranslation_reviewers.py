"""
Retrieve a list of pretranslated strings, get the list of reviewers with their
contact email address.

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon-staging ./manage.py shell
"""

from datetime import datetime
from django.utils.timezone import get_current_timezone
from pontoon.base.models import *

pt_users = User.objects.filter(
    email__in=[
        "pontoon-tm@example.com",
        "pontoon-gt@example.com",
    ]
)

START_DATE = "01/04/2023"
tz = get_current_timezone()
start_date = tz.localize(datetime.strptime(START_DATE, "%d/%m/%Y"))

pretranslations = (
    Translation.objects.filter(user__in=pt_users, date__gte=start_date)
    .filter(Q(approved=True) | Q(rejected=True))
    .prefetch_related("actionlog_set")
    .order_by("entity__resource__project", "locale__code", "pk")
)

reviewers = (
    ActionLog.objects
    .filter(
        translation__in=pretranslations,
        action_type__in=["translation:approved", "translation:rejected"]
    )
    .values_list("performed_by__email", flat=True)
    .distinct()
)

if reviewers:
    print("List of pretranslation reviewers (contact email addresses):")
    print("\n".join(reviewers))
