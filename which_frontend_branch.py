import re
import sys


MAIN_BRANCHES = ["dev", "uat", "master"]

DEFAULT_BRANCH = "dev"

HOTFIX_BRANCH_RE = re.compile("^hotfix-(uat|master)")


def is_hotfix_branch(branch):
    return bool(HOTFIX_BRANCH_RE.match(branch))


def get_hotfix_target(branch):
    return HOTFIX_BRANCH_RE.match(branch).groups()[0]


def get_frontend_branch(api_branch_name):
    if is_hotfix_branch(api_branch_name):
        return get_hotfix_target(api_branch_name)

    if api_branch_name in MAIN_BRANCHES:
        return api_branch_name

    return DEFAULT_BRANCH


if __name__ == "__main__":
    api_branch_name = sys.argv[1]
    print(get_frontend_branch(api_branch_name))
