"""
Send email to all users who submitted at least 5 approved translations in the last 12 months.
"""

from django.core.mail import EmailMultiAlternatives
from django.db.models import Count
from pontoon.base.models import *
from datetime import datetime

MIN_COUNT = 5
START_DATE = datetime(2023, 4, 15)

contributors = (
    Translation.objects.filter(
        date__gte=START_DATE,
        approved=True,
    )
    .values("user")
    .annotate(count=Count("user"))
    .distinct()
)

contributors_with_min_count = [
    c["user"] for c in contributors if c["count"] >= MIN_COUNT
]

users = User.objects.filter(pk__in=contributors_with_min_count).exclude(
    profile__email_communications_enabled=False
)

emails = [u.contact_email for u in users]

subject = "Localization Fireside Chat: we want your questions!"

text = """Hello localizers,

We are excited to announce that we are organizing another edition of our Localization Fireside Chat at the end of the month (exact date and time to be announced next week through all our communication channels listed below).

The meeting will be recorded to accommodate for availability and timezone issues. Here is the link to both the live and recorded session:
https://mozilla.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=a11ac265-b003-488a-9686-b1550169ca3e

If you’d like to submit any questions beforehand, you may do so here:
https://forms.gle/7hNSwBBRs6BvoxFW8

You will be able to ask questions live in our l10n Matrix channel, too:
https://chat.mozilla.org/#/room/#l10n-community:mozilla.org

Here is the list of our other communication channels where the day and time of the event will be announced as well:
- Mastodon: https://mozilla.social/@localization
- X: https://twitter.com/mozilla_l10n
- Discourse: https://discourse.mozilla.org/c/l10n/

Thank you,
Mozilla L10n Team

P.S. To stop receiving these messages, go to your Settings in Pontoon and disable Email communications.

"""

html = """Hello localizers,
<br><br>
We are excited to announce that we are organizing another edition of our Localization Fireside Chat at the end of the month (exact date and time to be announced next week through all our communication channels listed below).
<br><br>
The meeting will be recorded to accommodate for availability and timezone issues. <a href="https://mozilla.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id=a11ac265-b003-488a-9686-b1550169ca3e">Here</a> is the link to both the live and recorded session.
<br><br>
If you’d like to submit any questions beforehand, you may do so <a href="https://forms.gle/7hNSwBBRs6BvoxFW8">here</a>.
<br><br>
You will be able to ask questions live in our <a href="https://chat.mozilla.org/#/room/#l10n-community:mozilla.org">l10n Matrix channel</a>, too.
<br><br>
Here is the list of our other communication channels where the day and time of the event will be announced as well:<br>
- <a href="https://mozilla.social/@localization">Mastodon</a><br>
- <a href="https://twitter.com/mozilla_l10n">X</a><br>
- <a href="https://discourse.mozilla.org/c/l10n/">Discourse</a>
<br><br>
Thank you,<br>
Mozilla L10n Team<br><br>
P.S. To stop receiving these messages, go to your <a href="https://pontoon.mozilla.org/settings/">Settings in Pontoon</a> and disable Email communications.
"""

for email in emails:
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email="Mozilla L10n Team <team@pontoon.mozilla.com>",
        # Do not put the entire list into the "to" field
        # or everyone will see all email addresses.
        to=[email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send()
