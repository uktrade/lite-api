#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

update_git_submodules() {
  git_clone_base_url="https://codestar-connections.eu-west-2.amazonaws.com/git-http/$AWS_ACCOUNT_ID/eu-west-2/$CODESTAR_CONNECTION_ID/uktrade"

  git config --global credential.helper '!aws codecommit credential-helper $@'
  git config --global credential.UseHttpPath true

  cat <<EOF > ./.gitmodules
  [submodule "lite-content"]
  	path = lite_content
  	url = $git_clone_base_url/lite-content.git
  	branch = master
  [submodule "lite_routing"]
  	path = lite_routing
  	url = $git_clone_base_url/lite-routing.git
  	branch = main
  [submodule "django_db_anonymiser"]
  	path = django_db_anonymiser
  	url = $git_clone_base_url/django-db-anonymiser.git
EOF

  git submodule update --init --remote --recursive
}

update_pip_file_for_dbt_platform() {
  sed -i 's/\[packages\]/[packages]\nendesive = "~=1.5.9"\npython-pkcs11 = "~=0.7.0"\npykcs11 = "~=1.4.4"\n/' Pipfile
  pipenv lock
}

main() {
  update_git_submodules
  update_pip_file_for_dbt_platform
}

main
