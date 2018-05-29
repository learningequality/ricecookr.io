#!/usr/bin/env python
import os
import yaml
from sushichef import SIKANA_LANGUAGES

# Reading Studio API token from credentials/parameters.yml
with open("credentials/parameters.yml", "r") as f:
    parameters = yaml.load(f)
KOLIBRI_TOKEN = parameters["kolibri"]["token"]

# TODO(ivan): refactor this to send socket json --- can assume all channels running with --daemon
print('Running ALL Sikana channels.... this will take many hours')
for ln in SIKANA_LANGUAGES:
    print('\n\n***********\n***********\nRunning chef for language_code=', ln)
    os.system("./sushichef.py -v --reset --stage --thumbnails --token={} language_code={}".format(KOLIBRI_TOKEN, ln))