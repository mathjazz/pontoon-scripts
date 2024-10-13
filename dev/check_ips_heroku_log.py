"""
In case of DDOS, this script can be used to check which IPs are generating more
traffic than usual. By default, IPs with at least 10 occurrences are listed.

1) Download a portion of the log from Heroku and save it locally.
The easiest way is to use CLI, e.g.

timeout 60 heroku logs --tail --app mozilla-pontoon > log.txt

On macOS you might need to run `brew install coreutils` to get `timeout`.

This command works around Heroku's 1500 lines limit, reading the log for 60
seconds instead.

Alternative methods here: https://devcenter.heroku.com/articles/logging#view-logs

2) Populate `blocked_ip_setting` with the IPs stored in the mozilla-pontoon app
settings.

Open https://dashboard.heroku.com/apps/mozilla-pontoon/resources

Click `Reveal Config Vars`, then search for `BLOCKED_IPS`, and copy & paste the
value as is.

3) Update the `BLOCKED_IPS` config var with listed IP addresses.

Usage:
    python check_ips_heroku_log.py log.txt
    python check_ips_heroku_log.py --threshold 50 log.txt
"""

from ipaddress import ip_address, ip_network
from os.path import isfile
import argparse
import re
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "log_file",
        help="Path to log file",
    )
    parser.add_argument(
        "--threshold",
        required=False,
        default=10,
        help="Threshold under which IPs are ignored",
    )
    args = parser.parse_args()
    threshold = int(args.threshold)
    log_file = args.log_file

    if not isfile(log_file):
        sys.exit(f"File {log_file} doesn't exist.")

    ips = {}
    filter = re.compile(r"fwd=\"([\d.]+)\"")

    # Copy from Heroku settings
    blocked_ip_setting = ""

    BLOCKED_IPS = []
    BLOCKED_IP_RANGES = []
    for ip in blocked_ip_setting.split(","):
        ip = ip.strip()
        if ip == "":
            continue
        try:
            # If the IP is valid, store it directly as string
            ip_obj = ip_address(ip)
            BLOCKED_IPS.append(ip)
        except ValueError:
            try:
                # Check if it's a valid IP range (CIDR notation)
                ip_obj = ip_network(ip, strict=False)
                BLOCKED_IP_RANGES.append(ip_obj)
            except ValueError:
                print(f"Invalid IP or IP range defined in BLOCKED_IPS: {ip}")

    with open(log_file) as f:
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

    output = {
        "high": {"message": "\nIPs with high activity:", "ips": []},
        "blocked": {"message": "\nIPs already blocked by current settings:", "ips": []},
    }
    for ip, count in sorted_ips.items():
        try:
            ip_obj = ip_address(ip)
        except ValueError:
            print(f"Invalid IP extracted from log: {ip}")
            continue

        # Ignore IPs below threshold
        if count < threshold:
            continue

        # Ignore IPs already blocked
        blocked = False
        if ip in BLOCKED_IPS:
            blocked = True
        for ip_range in BLOCKED_IP_RANGES:
            if ip_obj in ip_range:
                blocked = True

        type = "blocked" if blocked else "high"
        output[type]["ips"].append(f"  {ip}: {count}")

    for data in output.values():
        print(data["message"])
        if data["ips"]:
            print("\n".join(data["ips"]))
        else:
            print("  -")


if __name__ == "__main__":
    main()
