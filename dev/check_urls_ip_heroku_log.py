"""
This script can be used to extract the paths requested by the specified IP.

Download a portion of the log from Heroku and save it locally.
The easiest way is to use CLI, e.g.

timeout 60 heroku logs --tail --app mozilla-pontoon > log.txt

On macOS you might need to run `brew install coreutils` to get `timeout`.

This command works around Heroku's 1500 lines limit, reading the log for 60
seconds instead.

Alternative methods here: https://devcenter.heroku.com/articles/logging#view-logs

Usage:
    python check_paths_ip_heroku_log.py log.txt 192.168.0.1
"""

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
        "--ip",
        required=True,
        help="IP to check",
    )
    args = parser.parse_args()
    log_file = args.log_file

    if not isfile(log_file):
        sys.exit(f"File {log_file} doesn't exist.")

    paths = {}
    filter = re.compile(r"path=\"([^\"]*)\".*fwd=\"([\d.]+)\"")

    with open(log_file) as f:
        content = f.readlines()
        for line in content:
            match = filter.search(line)
            if match:
                path = match.group(1)
                ip = match.group(2)
                if ip == args.ip:
                    if path not in paths:
                        paths[path] = 1
                    else:
                        paths[path] += 1

    sorted_paths = dict(sorted(paths.items(), key=lambda item: item[1], reverse=True))

    for path, count in sorted_paths.items():
        print(f"Path ({count}): {path}")


if __name__ == "__main__":
    main()
