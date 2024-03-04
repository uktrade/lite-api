#!/bin/bash

# The symbolic links to pg_dump and psql are not correctly setup for some reason
rm /home/vcap/deps/0/bin/pg_dump
ln -s /home/vcap/deps/0/apt/usr/lib/postgresql/12/bin/pg_dump /home/vcap/deps/0/bin/pg_dump

rm /home/vcap/deps/0/bin/psql
ln -s /home/vcap/deps/0/apt/usr/lib/postgresql/12/bin/psql /home/vcap/deps/0/bin/psql

python manage.py dump_and_anonymise
