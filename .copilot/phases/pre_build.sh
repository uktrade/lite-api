#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

export GIT_CLONE_BASE_URL="https://codestar-connections.eu-west-2.amazonaws.com/git-http/730335529260/eu-west-2/192881c6-e3f2-41a9-9dcb-fcc87d8b90be/uktrade"

git config --global credential.helper '!aws codecommit credential-helper $@'
git config --global credential.UseHttpPath true

echo "pulling submodules"
pwd

git submodule update --init --remote --recursive

echo "done"
ls -al

