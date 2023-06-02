"""
Retrieve a list of pretranslated strings and print its metadata.

This is used form manual scoring at end of the beta phase.

Output is formatted as CSV with the following columns:

* Project slug
* Locale code
* String URL
* Source string
* Rejected translation
* Approved translation
* Score
* Notes

Run the script in Pontoon's Django shell, e.g.: heroku run --app mozilla-pontoon
./manage.py shell
"""

from datetime import datetime
from django.utils.timezone import get_current_timezone
from pontoon.base.models import *

pt_users = User.objects.filter(
    email__in=[
        "pontoon-tm@example.com",
        "pontoon-gt@example.com",
    ]
)

START_DATE = "01/04/2023"
tz = get_current_timezone()
start_date = tz.localize(datetime.strptime(START_DATE, "%d/%m/%Y"))

pretranslations = (
    Translation.objects.filter(user__in=pt_users, date__gte=start_date)
    .filter(Q(rejected=True))
    .prefetch_related("actionlog_set")
    .order_by("entity__resource__project", "locale__code", "pk")
)

output = [
    "Project,Locale,String,Source String,Rejected Translation,Approved Translation,Score,Notes"
]
for t in pretranslations:
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
    # Single double quote needs to be replaced by a double quote for escaping in
    # CSV. Also strip new line characters from strings.
    source_string = t.entity.string.replace('"', '""').strip()
    rejected_translation = t.string.replace('"', '""').strip()
    try:
        approved_translation = Translation.objects.get(entity=entity, approved=True, locale=t.locale)
        approved_translation = str(approved_translation).replace('"', '""').strip()
    except Translation.DoesNotExist:
        approved_translation = "N/A"
    output.append(f'{project},{locale},{url},"{source_string}","{rejected_translation}","{approved_translation}",,')

print("\n".join(output))
