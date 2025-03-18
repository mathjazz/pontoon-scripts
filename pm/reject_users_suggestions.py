"""
Reject all unreviewed suggestions submitted by a given user.
"""

from django.contrib.auth.models import User
from django.utils import timezone

from pontoon.actionlog.models import ActionLog
from pontoon.base.models import Translation

USER_EMAIL = ""
ADMIN_EMAIL = ""

try:
    user = User.objects.get(email=USER_EMAIL)
except User.DoesNotExist:
    print("User does not exist. Abort.")
    exit()

try:
    admin = User.objects.get(is_superuser=True, email=ADMIN_EMAIL)
except User.DoesNotExist:
    print("Admin does not exist. Abort.")
    exit()

translations = Translation.objects.filter(
    user=user,
    approved=False,
    rejected=False,
)

# Log rejecting actions
actions_to_log = [
    ActionLog(
        action_type=ActionLog.ActionType.TRANSLATION_REJECTED,
        performed_by=admin,
        translation=t,
    )
    for t in translations
]
ActionLog.objects.bulk_create(actions_to_log)

# Reject suggestions
count = translations.update(
    active=False,
    rejected=True,
    rejected_user=admin,
    rejected_date=timezone.now(),
    approved=False,
    approved_user=None,
    approved_date=None,
    pretranslated=False,
    fuzzy=False,
)

print(f"{count} suggestions rejected.")
