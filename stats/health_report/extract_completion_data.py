#!/usr/bin/env python3

import json
import os
import sys
from urllib.parse import quote as urlquote
from urllib.request import urlopen


def main():
    projects = [
        "firefox-for-android",
        "firefox-for-ios",
        "firefox-monitor-website",
        "firefox-relay-website",
        "firefox",
        "mozilla-accounts",
        "mozilla-vpn-client",
    ]

    # Get stats from Pontoon
    query = """
{
    projects {
        name
        slug
        localizations {
            locale {
                code
            },
            approvedStrings,
            stringsWithWarnings,
            missingStrings,
            pretranslatedStrings,
            totalStrings
        }
    }
}
"""
    locale_data = {}
    try:
        print("Reading Pontoon stats...")
        url = f"https://pontoon.mozilla.org/graphql?query={urlquote(query)}&raw"
        response = urlopen(url)
        json_data = json.load(response)

        for project in json_data["data"]["projects"]:
            slug = project["slug"]
            if slug not in projects:
                continue

            for e in project["localizations"]:
                locale = e["locale"]["code"]
                if locale not in locale_data:
                    locale_data[locale] = {
                        "projects": 0,
                        "missing": 0,
                        "approved": 0,
                        "pretranslated": 0,
                        "total": 0,
                        "completion": 0,
                    }
                locale_data[locale]["missing"] += e["missingStrings"]
                locale_data[locale]["pretranslated"] += e["pretranslatedStrings"]
                locale_data[locale]["approved"] += (
                    e["approvedStrings"] + e["stringsWithWarnings"]
                )
                locale_data[locale]["total"] += e["totalStrings"]
                locale_data[locale]["projects"] += 1
    except Exception as e:
        print(e)

    # Calculate completion percentage
    for locale in locale_data:
        if locale_data[locale]["total"] > 0:
            locale_data[locale]["completion"] = round(
                (locale_data[locale]["approved"] / locale_data[locale]["total"]) * 100,
                2,
            )
        else:
            locale_data[locale]["completion"] = 0

    output = []
    output.append("Locale,Number of Projects,Completion,Approved strings,Total Strings")
    for locale in sorted(list(locale_data.keys())):
        locale_stats = locale_data[locale]
        output.append(
            f"{locale},{locale_stats['projects']},{locale_stats['completion']},{locale_stats['approved']},{locale_stats['total']}"
        )

    # Save locally
    with open("output.csv", "w") as f:
        f.write("\n".join(output))
        print("Data stored as output.csv")


if __name__ == "__main__":
    main()
