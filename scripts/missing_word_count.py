"""
Missing string and word count for given locales.
"""
for l in LOCALES:
    translated = Translation.objects.filter(
        entity__resource__project__slug="mozillaorg",
        locale__code=l,
        approved=True,
    ).values_list("entity__pk", flat=True)
    entities = Entity.objects.filter(
        resource__project__slug="mozillaorg",
        resource__translatedresources__locale__code=l,
        obsolete=False,
    ).exclude(pk__in=translated)
    print(
        "{}\t\t{}\t\t{}".format(
            l, entities.count(), sum([e.word_count for e in entities])
        )
    )
