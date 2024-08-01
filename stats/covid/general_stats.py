"""
Get the monthly number of new registrations, active users, submitted
translations, and strings added.

Output is formatted as CSV with the following columns:
* Period (month, year)
* Number of new user registered
* Number of active users
* Number of all translations submitted (includes pretranslations and suggestions, excludes imported)
* Number of approved translations submitted
* Number of strings added

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

import datetime

from collections import defaultdict

from django.db.models import Count
from django.db.models.functions import TruncMonth

from pontoon.base.models import *


data = {}

# New User Registrations
users = (
    User.objects.all()
    .annotate(period=TruncMonth("date_joined"))
    .values("period")
    .annotate(count=Count("id"))
    .order_by("period")
)
for x in users:
    period = "{}-{:02d}".format(x["period"].year, x["period"].month)
    if not period in data:
        data[period] = {}
    data[period]["registrations"] = x["count"]

# Active Users
translations = (
    Translation.objects.filter(user__isnull=False)
    .annotate(period=TruncMonth("date"))
    .values("period", "user_id")
    .annotate(count=Count("user_id"))
    .values("period", "count")
    .order_by("period")
)

translations_dict = defaultdict(list)
for x in translations:
    translations_dict[x["period"]].append(x["count"])

for y in translations_dict.items():
    period = "{}-{:02d}".format(y[0].year, y[0].month)
    if not period in data:
        data[period] = {}
    data[period]["active"] = len(y[1])

# New Entity Creations
entities = (
    Entity.objects.annotate(period=TruncMonth("date_created"))
    .values("period")
    .annotate(count=Count("id"))
    .order_by("period")
)

for x in entities:
    period = "{}-{:02d}".format(x["period"].year, x["period"].month)
    if not period in data:
        data[period] = {}
    data[period]["added"] = x["count"]

# New Translation Submissions
translations = (
    Translation.objects.filter(user__isnull=False)
    .annotate(period=TruncMonth("date"))
    .values("period")
    .annotate(count=Count("id"))
    .order_by("period")
)
for x in translations:
    period = "{}-{:02d}".format(x["period"].year, x["period"].month)
    if not period in data:
        data[period] = {}
    data[period]["all_translations"] = x["count"]

# Approved Translation Submissions
translations = (
    Translation.objects.filter(user__isnull=False, approved=True)
    .annotate(period=TruncMonth("date"))
    .values("period")
    .annotate(count=Count("id"))
    .order_by("period")
)
for x in translations:
    period = "{}-{:02d}".format(x["period"].year, x["period"].month)
    if not period in data:
        data[period] = {}
    data[period]["approved_translations"] = x["count"]

# Generate output
output = []
output.append(
    "Period,New User Registrations,Active Users,All Translations Submitted,Approved Translations Submitted,Strings Added"
)
periods = list(data.keys())
periods.sort()
for period in periods:
    period_data = data[period]
    registrations = (
        period_data["registrations"] if "registrations" in period_data else 0
    )
    active = period_data["active"] if "active" in period_data else 0
    all_translations = period_data["all_translations"] if "all_translations" in period_data else 0
    approved_translations = period_data["approved_translations"] if "approved_translations" in period_data else 0
    added = period_data["added"] if "added" in period_data else 0
    output.append(
        "{},{},{},{},{},{}".format(
            period,
            registrations,
            active,
            all_translations,
            approved_translations,
            added,
        )
    )

# Print output
print("\n".join(output))
