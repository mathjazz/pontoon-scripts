"""
Send email to listed users.
"""

from django.core.mail import EmailMultiAlternatives

emails = ['email1@example.com', ...]

subject = "Request for feedback: Community Health Dashboard"

text = u"""Hi,

We are working on Community Health Dashboards to help you and other locale managers identify issues within the community related to translation and review activity.

Please find the feature spec and the prototype on Discourse:
https://discourse.mozilla.org/t/request-for-feedback-locale-health-dashboard-for-managers/70197

Thanks,
L10n-drivers
"""

html = u"""Hi,
<br><br>
We are working on Community Health Dashboards to help you and other<br>
locale managers identify issues within the community related to<br>
translation and review activity.
<br><br>
Please find the feature spec and the prototype on <a href="https://discourse.mozilla.org/t/request-for-feedback-locale-health-dashboard-for-managers/70197">Discourse</a>.
<br><br>
Thanks,<br>
L10n-drivers
"""

for email in emails:
  msg = EmailMultiAlternatives(
    subject=subject,
    body=text,
    from_email='Pontoon Team <pontoon-team@mozilla.com>',
    # Do not put the entire list into the "to" field
    # or everyone will see all email addresses.
    to=[email]
  )
  msg.attach_alternative(html, 'text/html')
  msg.send()
