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
            help='Open coverage report after it has been collected',
            type=str
        )

    def handle(self, *args, **options):
        bash_script = ['pipenv', 'run', 'coverage', 'run', '--branch', '--source=./', 'manage.py', 'test']

        if options['coverage_to_collect']:
            bash_script[5] = '--source=./' + options['coverage_to_collect'] + '/'
            if options['tests_to_run']:
                if str(options['tests_to_run']) != 'all':
                    bash_script.append(options['tests_to_run'])
            else:
                bash_script.append(options['coverage_to_collect'])

        print(' '.join(bash_script))

        subprocess.call(bash_script)
        if options['html'] != "False":
            subprocess.call(['pipenv', 'run', 'coverage', 'html'])
            subprocess.call(['open', 'htmlcov/index.html'])
        else:
            subprocess.call(['pipenv', 'run', 'coverage', 'report'])
