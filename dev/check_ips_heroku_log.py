"""
In case of DDOS, this script can be used to check if IPs are generating more
traffic than usual.

1) Download a portion of the log from Heroku and save it locally.
THe easiest way is to use CLI, e.g.

heroku logs --app mozilla-pontoon -n 50000 > log.txt

Alternative methods here: https://devcenter.heroku.com/articles/logging#view-logs

2) Populate `blocked_ips` with the IPs stored in the mozilla-pontoon app
   settings.

Open https://dashboard.heroku.com/apps/mozilla-pontoon/resources

Click `Reveal Config Vars`, then search for `BLOCKED_IPS`, copy and past the
value as is.

Usage:
    check_ips_heroku_log log.txt
"""

import re
import sys

if len(sys.argv) == 1:
    sys.exit("Provide the log file as an argument")

ips = {}
filter = re.compile(r"fwd=\"([\d.]+)\"")
threshold = 10
# From Heroku settings
blocked_ips=""

with open(sys.argv[1]) as f:
    content = f.readlines()
    for line in content:
        match = filter.search(line)
        if match:
            ip = match.group(1)
            if ip not in ips:
                ips[ip] = 1
            else:
                ips[ip] += 1

sorted_ips = dict(sorted(ips.items(), key=lambda item: item[1], reverse=True))
blocked_ips = blocked_ips.split(",")

print(f"Ignoring IPs listed less than {threshold} times or already blocked.")
for ip, count in sorted_ips.items():
    if count < threshold or ip in blocked_ips:
        continue
    print(f"{ip}: {count}")
