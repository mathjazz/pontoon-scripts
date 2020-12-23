"""
A script used to extract data relevant for insights from legacy DB dumps.

Load the DB DUMP:
make loaddb DB_DUMP_FILE=path/to/my/dump

If needed, checkout old pontoon revision to prevent DB integrity errors:
git checkout `git rev-list -n 1 --before="2020-01-24 00:00" master`

IMPORTANT: Set `DATE` variable to the date of the DB dump before running the script.

Use printed data in insights-legacy-collect.py.
"""

from collections import defaultdict
from datetime import timedelta
from pontoon.base.utils import aware_datetime


DATE = aware_datetime(2020, 1, 24)


def group_dict_by(list_of_dicts, key):
    group = defaultdict(list)
    for dictionary in list_of_dicts:
        group[dictionary[key]].append(dictionary)
    return group


def get_lifespan(end_of_today, suggestions):
    """Get average age of the unreviewed suggestion."""
    unreviewed_suggestions_lifespan = timedelta()
    suggestion_count = len(suggestions)
    if suggestion_count > 0:
        total_suggestion_age = timedelta()
        for s in suggestions:
            total_suggestion_age += end_of_today - s["date"]
        unreviewed_suggestions_lifespan = total_suggestion_age / suggestion_count
    return unreviewed_suggestions_lifespan

end_of_today = DATE + timedelta(days=1)
data = {}
locales = Locale.objects.available()

stats = group_dict_by(
    locales
    .values(
        "pk",
        "total_strings",
        "approved_strings",
        "fuzzy_strings",
        "strings_with_errors",
        "strings_with_warnings",
        "unreviewed_strings",
    ),
    "pk",
)

suggestions = group_dict_by(
    Translation.objects.filter(
        # Make sure TranslatedResource is still enabled for the locale
        locale=F('entity__resource__translatedresources__locale'),
        approved=False,
        fuzzy=False,
        rejected=False,
        entity__obsolete=False,
        entity__resource__project__disabled=False,
        entity__resource__project__system_project=False,
        entity__resource__project__visibility="public",
    )
    .values("locale", "date"),
    "locale",
)

for locale in locales:
    data[locale.pk] = {
        "stats": stats[locale.pk],
        "lifespan": get_lifespan(end_of_today, suggestions[locale.pk])
    }

data

