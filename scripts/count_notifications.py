"""
Count the number of notifications sent within a period of time,
and the number of recipients who read them.
"""

from pontoon.base.models import *
from notifications.models import Notification
from datetime import datetime

START = datetime(2021, 4, 5)
END = datetime(2021, 4, 19)

notifications = Notification.objects.filter(
    timestamp__gte=START,
    timestamp__lte=END,
)

read_notifications = notifications.filter(unread=False)

notifications.count()
read_notifications.count()

recipients = notifications.values_list("recipient").distinct()
read_recipients = read_notifications.values_list("recipient").distinct()

recipients.count()
read_recipients.count()

logged_in = User.objects.filter(last_login__gte=START)
logged_in.count()
