from subprocess import call as execute_bash_command

from django.core.management import BaseCommand


class Command(BaseCommand):
    """
    pipenv run ./manage.py coverage <module_to_run_coverage_on> <tests_to_run>
    """

    def __init__(self):
        super().__init__()
        self.DEFAULT_THRESHOLD = "80"  # Default value for minimum code-coverage

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("module_to_run_coverage_on", nargs="?", type=str)
        parser.add_argument("tests_to_run", nargs="?", type=str)

        # Named (optional) arguments
        parser.add_argument(
            "--html", help="String representing if the report generated should be in HTML format", type=str,
        )

        parser.add_argument(
            "--threshold",
            help="String representing what minimum value the code-coverage must be in order to pass",
            type=str,
        )

    def handle(self, *args, **options):
        module_to_run_coverage_on = options["module_to_run_coverage_on"]
        tests_to_run = options["tests_to_run"] if options["tests_to_run"] else module_to_run_coverage_on
        self._gather_coverage(module_to_run_coverage_on, tests_to_run)

        report_type = "html" if not options["html"] or options["html"] != "False" else "report"
        threshold = options["threshold"] if options["threshold"] else self.DEFAULT_THRESHOLD
        self._show_report(report_type, threshold)

    @classmethod
    def _gather_coverage(cls, module_to_run_coverage_on, tests_to_run):
        gather_coverage_command = (
            "pipenv run coverage run --source=./"
            + (module_to_run_coverage_on if module_to_run_coverage_on else "")
            + " manage.py test --parallel=1"
        )

        if tests_to_run and tests_to_run != "all":
            gather_coverage_command.append(tests_to_run)

        print("\n`" + gather_coverage_command + "`\n")
        execute_bash_command(gather_coverage_command, shell=True)

    @classmethod
    def _show_report(cls, report_type, threshold):
        report_coverage_command = "pipenv run coverage " + report_type + " --fail-under=" + threshold
        print("\n`" + report_coverage_command + "`\n")

        status = execute_bash_command(report_coverage_command, shell=True)

        if report_type == "html":
            color = "red" if status == 2 else "green"

            s = open("htmlcov/index.html").read()
            s = s.replace("<h1>", '<h1 style="color: ' + color + '">')
            f = open("htmlcov/index.html", "w")
            f.write(s)
            f.close()

            execute_bash_command("open htmlcov/index.html", shell=True)
        else:
            message = (
                f"\n\n--FAILURE--\nCoverage was less than {threshold}%\n"
                if status == 2
                else f"\n\n--SUCCESS--\nCoverage was more than{threshold}%\n"
            )
            print(message)

        exit(status)
