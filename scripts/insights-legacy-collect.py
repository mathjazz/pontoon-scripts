"""
Collect data needed for the Insights tab from data produced by the
insights-legacy-extract.py script and stored into variables like
data_2020_01_23, data_2020_04_20, data_2020_11_12, data_2020_12_21.

The RECENT variable contains the export of the ./manage.py dumpdata insights.
"""

import datetime

from calendar import monthrange
from collections import namedtuple
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models.functions import TruncMonth

from pontoon.actionlog.models import ActionLog
from pontoon.base.models import Entity, Locale
from pontoon.base.utils import aware_datetime, group_dict_by
from pontoon.insights.models import LocaleInsightsSnapshot


Date = namedtuple("Date", ["year", "month", "day"])
YEAR = 2020


class Command(BaseCommand):
    help = """Collect legacy data needed for the Insights tab."""

    def handle(self, *args, **options):
        locales = Locale.objects.available()

        sync_user = User.objects.get(email="pontoon-sync@example.com").pk

        # Format recent backup
        data_14_to_20 = {
            "14": {},
            "15": {},
            "16": {},
            "17": {},
            "18": {},
            "19": {},
            "20": {},
            "21": {},
        }
        for r in RECENT:
            day = r["fields"]["created_at"][8:]
            locale = r["fields"]["locale"]
            data_14_to_20[day][locale] = {"stats": [r["fields"]]}

        self.stdout.write("COLLECTING ENTITIES...")

        all_entities = self.get_entities()

        self.stdout.write("ENTITIES COLLECTED")

        # Collect insights for each day
        for date in self.all_dates_in_year(YEAR):
            # We start collecting data properly on Dec 21, 2020
            if date.year == 2020 and date.month == 12 and date.day == 21:
                break

            if date.month in (1, 2, 3):
                backup = data_2020_01_23
                ubackup = backup
            elif date.month in (4, 5, 6, 7):
                backup = data_2020_04_20
                ubackup = backup
            elif date.month in (8, 9, 10, 11):
                backup = data_2020_11_12
                ubackup = backup
            elif date.month == 12:
                backup = data_2020_12_21
                ubackup = backup
                if date.day > 13:
                    backup = data_14_to_20[str(date.day)]

            end = aware_datetime(date.year, date.month, date.day)
            start = end - relativedelta(days=1)

            """Get actions of the given day, grouped by locale."""
            actions = self.get_actions(start, end)

            """Get entities of the given day, grouped by locale."""
            entities = all_entities[start]
            entities = group_dict_by(entities, "resource__translatedresources__locale")

            # Collect insights for each locale
            snapshots = []
            for locale in locales:
                (
                    human_translations,
                    machinery_translations,
                    new_suggestions,
                    peer_approved,
                    self_approved,
                    rejected,
                ) = self.get_activity_charts_data(actions[locale.id], end, sync_user)

                total_strings = 0
                approved_strings = 0
                fuzzy_strings = 0
                strings_with_errors = 0
                strings_with_warnings = 0
                unreviewed_strings = 0
                completion = 0.00
                unreviewed_suggestions_lifespan = datetime.timedelta()

                if locale.id in backup:
                    stats = backup[locale.id]["stats"][0]

                    total_strings = stats["total_strings"]
                    approved_strings = stats["approved_strings"]
                    fuzzy_strings = stats["fuzzy_strings"]
                    strings_with_errors = stats["strings_with_errors"]
                    strings_with_warnings = stats["strings_with_warnings"]
                    unreviewed_strings = stats["unreviewed_strings"]

                    completed_percent = 0
                    if stats["total_strings"]:
                        n = stats["approved_strings"] + stats["strings_with_warnings"]
                        completed_percent = n / stats["total_strings"] * 100
                    completion = round(completed_percent, 2)

                if locale.id in ubackup:
                    unreviewed_suggestions_lifespan = ubackup[locale.id]["lifespan"]

                snapshot = LocaleInsightsSnapshot(
                    locale=locale,
                    created_at=end,
                    # AggregatedStats
                    total_strings=total_strings,
                    approved_strings=approved_strings,
                    fuzzy_strings=fuzzy_strings,
                    strings_with_errors=strings_with_errors,
                    strings_with_warnings=strings_with_warnings,
                    unreviewed_strings=unreviewed_strings,
                    # Active users
                    # Unreviewed suggestions lifespan
                    unreviewed_suggestions_lifespan=unreviewed_suggestions_lifespan,
                    # Translation activity
                    completion=completion,
                    human_translations=len(human_translations),
                    machinery_translations=len(machinery_translations),
                    new_source_strings=len(entities[locale.id]),
                    # Review activity
                    peer_approved=len(peer_approved),
                    self_approved=len(self_approved),
                    rejected=len(rejected),
                    new_suggestions=len(new_suggestions),
                )

                snapshots.append(snapshot)

            LocaleInsightsSnapshot.objects.bulk_create(snapshots)

            self.stdout.write(
                "Day {}/{}/{}: insights created.".format(
                    date.year, date.month, date.day
                )
            )

    def all_dates_in_year(self, year=YEAR):
        """Get all dates in this year."""
        for month in range(1, 12 + 1):
            for day in range(1, monthrange(year, month)[1] + 1):
                yield Date(year, month, day)

    def get_entities(self):
        """Get all entities created this year, grouped by day."""
        entities = (
            Entity.objects.filter(
                date_created__gte=aware_datetime(YEAR, 1, 1),
                obsolete=False,
                resource__project__disabled=False,
                resource__project__system_project=False,
                resource__project__visibility="public",
            )
            .annotate(day=TruncMonth("date_created"))
            .values("pk", "resource__translatedresources__locale", "day")
        )

        return group_dict_by(entities, "day")

    def get_actions(self, start, end):
        """Get actions of the given day, grouped by locale."""
        actions = ActionLog.objects.filter(
            created_at__gte=start,
            created_at__lt=end,
            translation__entity__resource__project__system_project=False,
            translation__entity__resource__project__visibility="public",
        ).values(
            "action_type",
            "performed_by",
            "translation",
            "translation__locale",
            "translation__machinery_sources",
            "translation__user",
            "translation__approved_user",
            "translation__approved_date",
        )

        return group_dict_by(actions, "translation__locale")

    def get_activity_charts_data(self, activity_actions, end, sync_user):
        """Get data for Translation activity and Review activity charts."""
        human_translations = set()
        machinery_translations = set()
        new_suggestions = set()
        peer_approved = set()
        self_approved = set()
        rejected = set()

        for action in activity_actions:
            action_type = action["action_type"]
            performed_by = action["performed_by"]
            translation = action["translation"]
            machinery_sources = action["translation__machinery_sources"]
            user = action["translation__user"]
            approved_user = action["translation__approved_user"]
            approved_date = action["translation__approved_date"]

            # Review actions performed by the sync process are ignored, because they
            # aren't explicit user review actions.
            performed_by_sync = performed_by == sync_user

            if action_type == "translation:created":
                if len(machinery_sources) == 0:
                    human_translations.add(translation)
                else:
                    machinery_translations.add(translation)

                if not approved_date or approved_date > end:
                    new_suggestions.add(translation)

                # Self-approval can also happen on translation submission
                if performed_by == approved_user and not performed_by_sync:
                    self_approved.add(translation)

            elif action_type == "translation:approved" and not performed_by_sync:
                if performed_by == user:
                    self_approved.add(translation)
                else:
                    peer_approved.add(translation)

            elif action_type == "translation:rejected" and not performed_by_sync:
                rejected.add(translation)

        return (
            human_translations,
            machinery_translations,
            new_suggestions,
            peer_approved,
            self_approved,
            rejected,
        )
