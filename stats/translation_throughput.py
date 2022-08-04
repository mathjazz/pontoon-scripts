"""
https://bugzilla.mozilla.org/show_bug.cgi?id=1704859

For each Firefox locale, gather non-imported translations of 5-star priority source strings imported within the last 12 months. Then:

1. For each approved translation, calculate average time difference between translation approval and source string import.

2. For each translation that was submitted first for the string, calculate average time difference between translation submission and source string import.

3. Calculate average review time for each reviewed (i.e. approved or rejected) translation.
"""

import datetime

from django.db.models import Avg, DurationField, ExpressionWrapper, F, Min
from django.utils import timezone
from pontoon.base.models import *
from pontoon.base.utils import group_dict_by

a_year_ago = timezone.now() - datetime.timedelta(days=365)
locales = Project.objects.get(slug="firefox").locales.all()

def timedelta_to_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6) / 1e6

def seconds_to_days(seconds):
    return round(seconds / 86400, 2)

def divide_timedelta(td, divisor):
    total_seconds = timedelta_to_seconds(td)
    divided_seconds = round(total_seconds / float(divisor))
    return seconds_to_days(divided_seconds)

for l in locales.order_by("code"):
    translations = l.translation_set.filter(entity__date_created__gte=a_year_ago, entity__resource__project__priority=5).exclude(user=None)

    # Time to submit a translation
    approved_delta = F("approved_date") - F("entity__date_created")
    approved = (
        translations.filter(approved=True)
        .annotate(approved_delta=ExpressionWrapper(approved_delta, DurationField()))
        .aggregate(Avg("approved_delta"))
    )["approved_delta__avg"]
    if approved == None:
        approved = datetime.timedelta()

    # Time to submit a suggestion
    suggested_dates = translations.values('entity', 'entity__date_created').annotate(first_suggestion_date=Min('date'))
    suggested_count = len(suggested_dates)
    suggested = datetime.timedelta()
    if suggested_count > 0:
        total = datetime.timedelta()
        for s in suggested_dates:
            total += s['first_suggestion_date'] - s['entity__date_created']
        suggested = total / suggested_count

    # Average age of an unreviewed suggestion

    # Approved, but not self-approved
    approved_delta = (
        translations
        .filter(approved_date__isnull=False)
        .exclude(user=F('approved_user'))
    ).aggregate(
        average_delta=Avg(
            F('approved_date') - F('date')
        )
    )['average_delta']

    # Rejected, but not self-rejected
    rejected_delta = (
        translations
        .filter(rejected_date__isnull=False)
        .exclude(user=F('rejected_user'))
    ).aggregate(
        average_delta=Avg(
            F('rejected_date') - F('date')
        )
    )['average_delta']

    try:
        combined_delta = divide_timedelta(approved_delta + rejected_delta, 2)
    except TypeError:
        combined_delta = 0.0

    lifespan = str(combined_delta).replace(',', '')

    print(
        "{}, {}, {}, {}".format(
            l.code,
            seconds_to_days(timedelta_to_seconds((approved)),
            seconds_to_days(timedelta_to_seconds((suggested)),
            lifespan,
        )
    )
