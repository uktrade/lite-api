#!/usr/bin/env python

import boto3
import subprocess

s3_client = boto3.client('s3')

s3_client.download_file('lite-anonymiser-prod', 'test.sql', '/tmp/test.sql')

subprocess.run(['ls', '-al', '/tmp'])
