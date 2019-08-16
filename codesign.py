#!/usr/bin/env python
'''Hello world'''

import os
import sys
import subprocess


CONFIG = {
    'dart-sdk': {
        # pass in engine hash
        'cloud_path': lambda commit: 'gs://flutter_infra/flutter/%s/dart-sdk-darwin-x64' % commit,
        # pass in CWD
        'config_path': lambda cwd: '%s/' % cwd,
        }
    }


def sign_and_notarize(config):
    '''Invoke outside script to sign one archive'''
    command = [
        os.path.join(CWD, 'codesign-archive.py'),
        config['cloud_path'],
        config['config_path'],
        ]
    exit_code = subprocess.call(command)
    if exit_code != 0:
        print 'Error while trying to sign & notarize %s' % config['name']
        print 'Exited with code %i' % exit_code
        exit(exit_code)


def get_archive_configs(commands):
    '''Validate command line arguments are all specified in CONFIG constant, return config dict'''
    configs = []
    for command in commands:
        config = CONFIG.get(command, None)
        if config is None:
            print 'Archive %s is not recognized!' % command
            exit(1)
        configs.append({
            'name': command,
            'cloud_path': config['cloud_path'](commit),
            'config_path': config['config_path'](CWD),
            })

    return configs


def main(args):
    '''Application entrypoint'''
    if args[0] == 'all':
        args = list(CONFIG.keys())
    archive_configs = get_archive_configs(args)
    print archive_configs


CWD = os.getcwd()

if len(sys.argv) == 1:
    print 'Please provide arguments to specify which archives to sign.'
    exit(1)

main(sys.argv[1:])
