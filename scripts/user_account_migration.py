"""
Migrate data from one user account to another.
"""

from pontoon.base.models import *

OLD = 'old.email@example.com'
NEW = 'new.email@example.com'

old = User.objects.get(email=OLD)
new = User.objects.get(email=NEW)

Translation.objects.filter(user=old).update(user=new)
Translation.objects.filter(approved_user=old).update(approved_user=new)
Translation.objects.filter(unapproved_user=old).update(unapproved_user=new)
Translation.objects.filter(rejected_user=old).update(rejected_user=new)
Translation.objects.filter(unrejected_user=old).update(unrejected_user=new)

old.notifications.update(recipient=new)
