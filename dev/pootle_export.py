from django.core.management.base import (
    BaseCommand,
    CommandError,
    NoArgsCommand,
)
from optparse import make_option
from pootle_store.models import Store, Unit

import codecs
import json
import subprocess


class Command(BaseCommand):
    help = 'Export translation authors and dates for given Pootle project and locale.'

    option_list = NoArgsCommand.option_list + (
        make_option('--project', action='store', dest='project',
                    help='Project code to export translations from'),
        make_option('--locale', action='store', dest='locale',
                    help='Locale code to export translations from'),
        )

    def handle(self, *args, **options):
        project = options.get('project', False)
        locale = options.get('locale', False)

        if not project and not locale:
            raise CommandError('You must provide a project or a locale.')

        # For all projects enabled for locale
        if not project:
            projects = (
                Store.objects.filter(translation_project__language__code=locale)
                .values_list('translation_project__project__code', flat=True)
                .distinct()
            )

            for project in set(projects):
                self.handle_project_locale(project, locale)

            return False

        # For all locales enabled for project
        if not locale:
            locales = (
                Store.objects.filter(translation_project__project__code=project)
                .exclude(translation_project__language__code='templates')
                .values_list('translation_project__language__code', flat=True)
                .distinct()
            )

            for locale in set(locales):
                self.handle_project_locale(project, locale)

            return False

        if project and locale:
            self.handle_project_locale(project, locale)

    def handle_project_locale(self, project, locale):
        output = {}

        # Loop stores (files)
        for store in Store.objects.filter(
            translation_project__project__code=project,
            translation_project__language__code=locale
        ):

            path = {}

            # Loop units (original-translation pairs)
            for unit in Unit.objects.filter(store=store):
                if unit.state == 200 and unit.submitted_by:

                    path[unit.source_f] = {
                        "translation": unit.target_f,
                        "date": str(unit.submitted_on),
                        "author": unit.submitted_by.user.email
                    }

            output[store.path] = path

        filename = "%s_%s.json" % (locale, project)

        # Export to file
        with codecs.open("verbatim/" + filename, 'w+', 'utf-8') as f:
            f.seek(0)
            f.truncate()
            content = json.dumps(output, indent=4, ensure_ascii=False)
            f.write(content)

        # Commit to SVN
        try:
            s = subprocess.PIPE
            add = ["svn", "add", "verbatim/" + filename, "verbatim"]
            proc = subprocess.Popen(args=add, stdout=s, stderr=s, stdin=s)

            commit = ["svn", "commit", "-m", "Added " + filename, "verbatim"]
            proc = subprocess.Popen(args=commit, stdout=s, stderr=s, stdin=s)

            (output, error) = proc.communicate()
            code = proc.returncode
        except OSError as error:
            code = -1

        if code == 0:
            self.stdout.write("Committed " + filename + ".\n")
        else:
            self.stdout.write(error + "\n")
