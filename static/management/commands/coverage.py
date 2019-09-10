from django.core.management import BaseCommand
import subprocess

# 1. The first argument implies the coverage to be collected
# 2. The second argument implies the tests to be run in order to collect that coverage
# 3. If a second argument is not supplied, it will default to the same value as the first argument
# -- Examples --
# 1. `pipenv run ./manage.py cases` will collect coverage on the `cases` app and only run the `cases` tests
# 2. `pipenv run ./manage.py cases all` will collect coverage on the `cases` app and and run all tests
# 3. `pipenv run ./manage.py cases queues` will collect coverage on the `cases` app and only run the `queues` tests


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('coverage_to_collect', nargs='?', type=str)
        parser.add_argument('tests_to_run', nargs='?', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--html',
            help='Specify an HTML format for the report',
            type=bool
        )

        parser.add_argument(
            '--fail-under',
            help='Value representing what the coverage must exceed in order to pass',
            type=str
        )

    def handle(self, *args, **options):
        self._gather_coverage(options)
        self._show_report(options)

    def _gather_coverage(self, options):
        gather_coverage_script = ['pipenv', 'run', 'coverage', 'run', '--source=./', 'manage.py', 'test']
        if options['coverage_to_collect']:
            gather_coverage_script[4] = '--source=./' + options['coverage_to_collect'] + '/'
            if options['tests_to_run']:
                if options['tests_to_run'] != 'all':
                    gather_coverage_script.append(options['tests_to_run'])
            else:
                gather_coverage_script.append(options['coverage_to_collect'])

        print('\n%s%s%s' % ('`', ' '.join(gather_coverage_script), '`\n'))
        subprocess.call(gather_coverage_script)

    def _show_report(self, options):
        report_type = 'html' if options['html'] else 'report'
        fail_under = options['fail_under'] if options['fail_under'] else '80'
        report_coverage_script = ['pipenv', 'run', 'coverage', report_type,  '--fail-under=' + fail_under]
        print('\n%s%s%s' % ('`', ' '.join(report_coverage_script), '`\n'))

        if subprocess.call(report_coverage_script) == 2:
            print('\n\n--FAILURE--\nCoverage was less than ' + fail_under + '%\n')
        else:
            print('\n\n--SUCCESS--\nCoverage was more than ' + fail_under + '%\n')

        if 'html' in report_coverage_script:
            subprocess.call(['open', 'htmlcov/index.html'])
