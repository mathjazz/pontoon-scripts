"""
Email addresses of managers and translators."""

import datetime

from collections import defaultdict
from django.utils import timezone
from pontoon.base.models import * 

managers = defaultdict(set)
translators = defaultdict(set)

locales = Locale.objects.prefetch_related(
    Prefetch("managers_group__user_set", to_attr="fetched_managers"),
    Prefetch("translators_group__user_set", to_attr="fetched_translators"),
)

for locale in locales:
    for user in locale.translators_group.fetched_translators:
        if user.last_login > timezone.make_aware(datetime.datetime(2019,12,3)):
            translators[user].add(locale.code)
    for user in locale.managers_group.fetched_managers:
        managers[user].add(locale.code)

manager_emails = [u.email for u in managers.keys()]

translator_emails = [u.email for u in translators.keys()]
