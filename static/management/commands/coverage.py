import sys

from django.core.management import BaseCommand
import subprocess


class Command(BaseCommand):
    def __init__(self):
        super().__init__()
        self.DEFAULT_THRESHOLD = "80"  # Default value for minimum code-coverage

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('coverage_to_collect', nargs='?', type=str)
        parser.add_argument('tests_to_run', nargs='?', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--html',
            help='Boolean representing if the report generated should be in HTML format',
            type=bool
        )

        parser.add_argument(
            '--threshold',
            help='String representing what minimum value the code-coverage must be in order to pass',
            type=str
        )

    def handle(self, *args, **options):
        coverage_to_collect = options['coverage_to_collect']
        tests_to_run = options['tests_to_run'] if options['tests_to_run'] else coverage_to_collect
        self._gather_coverage(coverage_to_collect, tests_to_run)

        report_type = 'html' if options['html'] else 'report'
        threshold = options['threshold'] if options['threshold'] else self.DEFAULT_THRESHOLD
        self._show_report(report_type, threshold)

    def _gather_coverage(self, coverage_to_collect, tests_to_run):
        gather_coverage_script = ['pipenv', 'run', 'coverage', 'run',
                                  '--source=./' + (coverage_to_collect if coverage_to_collect else ''),
                                  'manage.py', 'test']

        if tests_to_run and tests_to_run != 'all':
            gather_coverage_script.append(tests_to_run)

        print('\n`' + (' '.join(gather_coverage_script)) + '`\n')
        subprocess.call(gather_coverage_script)

    def _show_report(self, report_type, threshold):
        report_coverage_script = ['pipenv', 'run', 'coverage', report_type, '--fail-under=' + threshold]
        print('\n`' + (' '.join(report_coverage_script)) + '`\n')
        status = subprocess.call(report_coverage_script)

        if report_type == 'html':
            subprocess.call(['open', 'htmlcov/index.html'])

        if status == 2:
            print('\n\n--FAILURE--\nCoverage was less than ' + threshold + '%\n')
            sys.exit(status)
        else:
            print('\n\n--SUCCESS--\nCoverage was more than ' + threshold + '%\n')
