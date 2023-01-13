"""
Retrieve a list of pretranslated strings and print its metadata.
Output is formatted as CSV with the following columns:

* Project slug
* Locale code
* String URL
* Translation time
* Review time
* Hours to review
* Status
* Rating
* Comment

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

import html
import math
from pontoon.base.models import *

pt_users = User.objects.filter(
    email__in=[
        "pontoon-tm@example.com",
        "pontoon-gt@example.com",
    ]
)

pretranslations = (
    Translation.objects.filter(user__in=pt_users)
    .filter(Q(approved=True) | Q(rejected=True))
    .prefetch_related("actionlog_set")
    .order_by("entity__resource__project", "locale__code", "pk")
)

for i, t in enumerate(pretranslations):
    if i == 0:
        print(
            "Project\tLocale\tString\tTranslation time\tReview time\tHours to review\tStatus\tRating\tComment"
        )
    entity = t.entity
    resource = entity.resource
    project = resource.project.slug
    locale = t.locale.code
    url = "https://pontoon.mozilla.org/{}/{}/{}?string={}".format(
        locale,
        project,
        resource.path,
        entity.pk,
    )
    translation_time = t.date
    if t.approved:
        action_type = "translation:approved"
    else:
        action_type = "translation:rejected"
    review_time = t.actionlog_set.filter(action_type=action_type).first().created_at
    time_to_review = (review_time - translation_time).total_seconds()
    status = "approved" if t.approved else "rejected"
    comment = t.comments.first()
    comment_content = str(
        html.unescape(comment.content.removeprefix("<p>").removesuffix("</p>"))
        if comment
        else ""
    )
    rating = (
        "0" if status == "approved" else comment_content[0] if comment_content else ""
    )
    print(
        '{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t"{}"'.format(
            project,
            locale,
            url,
            translation_time.strftime("%d-%m-%Y %H:%M:%S"),
            review_time.strftime("%d-%m-%Y %H:%M:%S"),
            math.ceil(time_to_review / 3600),
            status,
            rating,
            comment_content,
        )
    )
