"""
How many new strings and words have been added to a project each month,
and how many of these words had a 70%+, 80%+, 90%+ or 100% match in TM.
"""

from dateutil.relativedelta import relativedelta
from pontoon.base.models import Project, TranslationMemoryEntry, Entity
from pontoon.base.templatetags.helpers import as_simple_translation
from pontoon.base.utils import aware_datetime, get_last_months

months = sorted([aware_datetime(year, month, 1) for year, month in get_last_months(14)])

PROJECT = Project.objects.get(slug="mozillaorg")
print("month\t\tstr\t\twords\t\tno_tm\t\ttm70%+\t\ttm80%+\t\ttm90%+\t\ttm100%+")

for month in months:
    output = []
    entities = Entity.objects.filter(
        resource__project=PROJECT,
        date_created__gte=month,
        date_created__lt=month + relativedelta(months=1),
    )
    for e in entities:
        try:
            tm = (
                TranslationMemoryEntry.objects.filter(locale__code="de")
                .minimum_levenshtein_ratio(as_simple_translation(e.string))
                .exclude(entity=e)
                .exclude(translation__approved=False, translation__fuzzy=False)
                .filter(entity__date_created__lt=month)
                .order_by("-quality")
            )[0]
        except:
            tm = None
        output.append((e, tm))
    print(
        "{}\t\t{}\t\t{}\t\t{}\t\t{}\t\t{}\t\t{}\t\t{}".format(
            month.strftime("%B"),
            entities.count(),
            sum([e.word_count for e, _ in output]),
            sum([e.word_count for e, tm in output if tm is None]),
            sum(
                [
                    e.word_count
                    for e, tm in output
                    if tm is not None and tm.quality >= 70
                ]
            ),
            sum(
                [
                    e.word_count
                    for e, tm in output
                    if tm is not None and tm.quality >= 80
                ]
            ),
            sum(
                [
                    e.word_count
                    for e, tm in output
                    if tm is not None and tm.quality >= 90
                ]
            ),
            sum(
                [
                    e.word_count
                    for e, tm in output
                    if tm is not None and tm.quality == 100
                ]
            ),
        )
    )

"""
month       str     words   no_tm   tm70%+  tm80%+  tm90%+  tm100%+
January		49		844		511		333		330		222		74
February	192		6323	6068	255		224		141		124
March		63		696		289		407		398		379		325
April		50		395		277		118		102		57		54
May		    466		3014	1297	1717	1551	1131	781
June		540		12530	6017	6513	6334	5177	1727
July		400		4529	1425	3104	2889	2073	908
August		35		332		230		102		91		46		41
September	122		2406	882		1524	1471	1121	411
October		310		3672	1610	2062	1866	1367	1090
November	238		1940	362		1578	1364	923		508
December	500		13679	6517	7162	7025	6570    2933
"""
