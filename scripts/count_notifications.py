"""
Count the number of notifications sent within a period of time,
and the number of recipients who read them.
"""

from pontoon.base.models import *
from notifications.models import Notification
from datetime import datetime

notifications_h2_2020 = Notification.objects.filter(
    timestamp__gte=datetime(2020, 7, 1),
    timestamp__lte=datetime(2020, 12, 31),
)

read_notifications_h2_2020 = notifications_h2_2020.filter(unread=False)

notifications_h2_2020.count()
read_notifications_h2_2020.count()

notifications_h2_2020.values_list("recipient").distinct().count()
read_notifications_h2_2020.values_list("recipient").distinct().count()
