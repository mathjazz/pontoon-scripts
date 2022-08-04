"""
Send notifications to all users.
"""

import uuid

from django.contrib.auth.models import User
from notifications.models import Notification
from notifications.signals import notify

SENDER = "email@example.com"
sender = User.objects.get(email=SENDER)
users = User.objects.exclude(email="").exclude(email__regex=r"^pontoon-(\w+)@example.com$")

message = """
<a href="https://pontoon.mozilla.org/terms/">Pontoon's terms</a>
were updated to include the Mozilla Community Participation Guidelines.
Please <a href="https://pontoon.mozilla.org/terms/">take a look</a>.
"""

for index, recipient in enumerate(users):
    notify.send(
        sender,
        recipient=recipient,
        verb="has sent you a message",
        description=message,
        identifier=uuid.uuid4().hex
    )
    print index
