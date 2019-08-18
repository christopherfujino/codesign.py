#!/usr/bin/env python
'''Hello world'''

import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time

ARCHIVES = [
    {
        'path': 'darwin-x64/artifacts.zip',
        'files': [
            'gen_snapshot',
            ],
        'files_with_entitlements': [
            'flutter_tester',
            ],
        },
    {
        'path': 'android-arm-release/darwin-x64.zip',
        'files': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'ios-profile/artifacts.zip',
        'files': [
            'gen_snapshot_arm64',
            #'gen_snapshot',
            'gen_snapshot_armv7',
            {
                'path': 'Flutter.framework.zip',
                'files': [
                    'Flutter',
                    ]
                },
            ],
        },
    {
        'path': 'darwin-x64/FlutterMacOS.framework.zip',
        'files': [
            {
                'path': 'FlutterMacOS.framework.zip',
                'files': [
                    'Versions/A/FlutterMacOS',
                    ]
                }
            ],
        },
    {
        'path': 'android-arm64-release/darwin-x64.zip',
        'files': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'android-arm64-profile/darwin-x64.zip',
        'files': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'ios/artifacts.zip',
        'files': [
            {
                'path': 'Flutter.framework.zip',
                'files': [
                    'Flutter',
                    ],
                },
            'gen_snapshot_arm64',
            'gen_snapshot_armv7',
            ],
        },
    {
        'path': 'ios-release/artifacts.zip',
        'files': [
            'gen_snapshot_arm64',
            #'gen_snapshot',
            'gen_snapshot_armv7',
            {
                'path': 'Flutter.framework.zip',
                'files': [
                    'Flutter',
                    ]
                },
            ],
        },
    {
        'path': 'android-arm-profile/darwin-x64.zip',
        'files': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'dart-sdk-darwin-x64.zip',
        'files': [
            'dart-sdk/bin/snapshots/libtensorflowlite_c-mac64.so',
            ],
        'files_with_entitlements': [
            'dart-sdk/bin/dart',
            ]
        },
]

CWD = os.getcwd()

GOOGLE_STORAGE_BASE = 'gs://flutter_infra/flutter'

LOG = []


def log(str_or_list, output_logfile=None):
    '''Print to stdout and append to LOG list'''
    message = ''
    if isinstance(str_or_list, list):
        message = ''.join(str_or_list)
    elif isinstance(str_or_list, str):
        message = str_or_list
    else:
        log_and_exit('Unknown entity "%s" passed to log' % str_or_list)
    if output_logfile is None:
        LOG.append(message)
        print message
    else:
        dirname = os.path.dirname(output_logfile)
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        with open(output_logfile, 'w') as logfile:
            logfile.write(message)


def write_log_to_file(filename, should_append=False):
    '''Write everything in LOG to given file, then clear LOG'''
    mode = 'w'
    if should_append:
        mode = 'w+'
    with open(filename, mode) as logfile:
        if should_append:
            logfile.write('\n - NEW LOG - \n')
        logfile.write('\n'.join(LOG))
    del LOG[:]


def log_and_exit(message, exit_code=1):
    '''Flush log then exit'''
    log(message)
    write_log_to_file(os.path.join(get_logs_dir(), 'crasher.log'))
    exit(exit_code)


class Cd(object):
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.new_path = os.path.expanduser(newPath)
        self.saved_path = ''

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


def usage():
    '''Prints usage for this script'''

    print '''
    Usage:
    codesign.py <engine-commit-hash>
    '''


def validate_command(command_name):
    '''Validate the given command exists on PATH'''

    if subprocess.call(['which', command_name]) != 0:
        print 'You don\'t appear to have "%s" installed.' % command_name
        exit(1)


def clean():
    '''Clean our build folders'''
    for dirname in ['staging']:
        print os.path.join(CWD, dirname, '*')
        shutil.rmtree(dirname, ignore_errors=True)
        os.mkdir(dirname)


def ensure_entitlements_file():
    '''Write entitlements file if it does not exist'''
    entitlements_path = os.path.join(CWD, 'Entitlements.plist')
    if not os.path.isfile(entitlements_path):
        print 'Writing Entitlements.plist file...\n'
        entitlements_file = open(entitlements_path, 'w')
        entitlements_file.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>com.apple.security.cs.allow-jit</key>
        <true/>
        <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
        <true/>
    </dict>
</plist>
''')
        entitlements_file.close()


def get_unique_filename(url):
    '''Generates a filename based on input url'''
    return url.replace('/', '_')


def download(cloud_path, local_dest_path):
    '''Download supplied Google Storage URI'''
    if os.path.isfile(local_dest_path):
        log('Skipping download of %s, already exists locally\n' % cloud_path)
        return

    log('Downloading %s...\n' % cloud_path)

    command = [
        'gsutil',
        'cp',
        cloud_path,
        local_dest_path,
        ]
    exit_code = subprocess.call(command)
    if exit_code != 0:
        log_and_exit('Download of %s failed!' % cloud_path, exit_code)


def upload(local_path, cloud_path):
    '''Upload local_path to GCP cloud_path'''
    command = [
        'gsutil',
        'cp',
        local_path,
        cloud_path,
        ]
    exit_code = subprocess.call(command)
    if exit_code != 0:
        log_and_exit('Upload of %s failed!' % cloud_path, exit_code)


def read_json_file(file_path):
    '''Given the path to a JSON file, returns dict'''
    with open(file_path, 'r') as config_file:
        config_string = config_file.read()
        config_dict = json.loads(config_string)
        return config_dict


def create_staging_name(full_file_path):
    '''Given zip archive, create corresponding, adjacent staging dir'''
    return full_file_path + '.staging'


def unzip_archive(file_path):
    '''Calls subprocess to unzip archive'''
    archive_dirname = create_staging_name(file_path)
    exit_code = subprocess.call([
        'unzip',
        file_path,
        '-d',
        archive_dirname])
    if exit_code != 0:
        log_and_exit('Unzipping of %s failed' % file_path, exit_code)
    return archive_dirname


def get_binary_names(config):
    '''Returns names of binary files to sign/notarize from dict'''
    return config['binary_paths']


def validate_binary_exists(path):
    '''Validate a binary file listed in config exists'''
    return os.path.isfile(path)


def sign(path, with_entitlements=False):
    '''Sign a single binary'''
    command = [
        'codesign',
        '-f',  # force
        '-s',  # use the cert provided by next argument
        CODESIGN_CERT_NAME,
        path,
        '--timestamp',  # add a secure timestamp
        '--options=runtime',  # hardened runtime
        ]
    #if with_entitlements:
    command += ['--entitlements', './Entitlements.plist']
    exit_code = subprocess.call(command)
    if exit_code != 0:
        log_and_exit('Error while attempting to sign %s' % path, exit_code)


def run_and_return_output(command):
    '''Takes in list/string of command, returns list of stdout'''
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    return proc.stdout.readlines()


def get_logs_dir():
    '''Ensure exists, and return path to global logs dir'''
    log_dir = os.path.join(CWD, 'logs')
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)
    return log_dir


def zip_stats(path):
    '''Append hash and size stats to log'''
    log('Getting stats for %s...\n' % path)
    logfilename = os.path.join(
        get_logs_dir(),
        'zip_contents',
        '%f_%s.log' % (
            time.time(),
            os.path.basename(path)),
        )
    log(run_and_return_output(['unzip', '-l', path]), logfilename)


def update_zip(path, destination_path):
    '''Zips up a directory to the destination path'''
    with Cd(path):
        subprocess.call([
            'zip',
            '--symlinks',
            '-r',
            '-u',  # Update existing files if newer on file system
            destination_path,
            '.',
            '-i',
            '*',
            ])


def upload_zip_to_notary(archive_path):
    '''Uploads zip file to the notary service'''
    print 'Initiating upload of file %s...' % archive_path
    command = [
        'xcrun',
        'altool',
        '--notarize-app',
        '--primary-bundle-id',
        CODESIGN_PRIMARY_BUNDLE_ID,
        '--username',
        CODESIGN_USERNAME,
        '--password',
        APP_SPECIFIC_PASSWORD,
        '--file',
        archive_path,
        # Note that this tool outputs to STDERR, even on success
        ]
    proc = subprocess.Popen(command, stderr=subprocess.PIPE)
    out = '\n'.join(proc.stderr.readlines())
    print out

    match = re.search('RequestUUID = ([a-z0-9-]+)', out)
    if not match:
        log_and_exit('Unrecognized output from: %s' % ' '.join(command))

    request_uuid = match.group(1)
    print 'Your RequestUUID is: %s' % request_uuid

    return request_uuid


def poll_and_check_status(uuid):
    '''Poll and check the status of our request'''
    command = [
        'xcrun',
        'altool',
        '--notarization-info',
        uuid,
        '-u',
        CODESIGN_USERNAME,
        '--password',
        APP_SPECIFIC_PASSWORD,
        # Note that this tool outputs to STDERR, even on success
        ]
    timeout = 15

    # Checking immediately will lead to the request not being found
    print 'Pausing %i seconds until the first status check...\n' % timeout
    time.sleep(timeout)
    while True:
        log('Checking on the status of request: %s' % uuid)
        proc = subprocess.Popen(command, stderr=subprocess.PIPE)
        output = ''.join(proc.stderr.readlines())
        log(output)

        match = re.search('[ ]*Status: ([a-z ]+)', output)
        if not match:
            log_and_exit('Unrecognized output from: %s' % ' '.join(command))

        status = match.group(1)
        if status == 'success':
            return True
        elif status == 'in progress':
            print 'Notarization is still pending...\n'
        else:
            log_and_exit('Notarization failed with: %s' % status)

        print 'Pausing %i seconds until the next check...\n' % timeout
        time.sleep(timeout)


def notarize(archive_path):
    '''Notarize given archive zip'''
    request_uuid = upload_zip_to_notary(archive_path)
    start = time.time()
    poll_and_check_status(request_uuid)
    end = time.time()
    print 'Notarizing took %s' % str(datetime.timedelta(seconds=(end - start)))


def success_message(output_archive):
    '''Print success message.'''
    log('Your notarization of %s was successful.' % output_archive)


def process_archive(config, commit, working_dir, is_reentrant=False):
    '''Main execution'''
    input_cloud_path = '%s/%s/%s' % (
        GOOGLE_STORAGE_BASE,
        commit,
        config['path'])

    unique_filename = get_unique_filename(config['path'])
    zip_path = os.path.join(
        working_dir,
        unique_filename)

    log('Beginning processing of %s...\n' % config['path'])

    download(input_cloud_path, zip_path)

    log('Unzipping archive...\n')
    staging_dirname = unzip_archive(zip_path)

    log('Validating config...\n')
    files = config.get('files', [])
    files_with_entitlements = config.get('files_with_entitlements', [])
    for file_path in files + files_with_entitlements:
        if isinstance(file_path, dict):
            continue
        absolute_path = os.path.join(staging_dirname, file_path)
        if not validate_binary_exists(absolute_path):
            log_and_exit('Cannot find file %s from config' % absolute_path)

    log('Signing binaries...\n')
    for dictionary in [
            {
                'files': files,
                'entitlements': False,
                },
            {
                'files': files_with_entitlements,
                'entitlements': True,
                }]:
        for relative_path in dictionary['files']:
            if isinstance(relative_path, dict):
                process_archive(
                    relative_path,  # this is actually a dict, not a path
                    commit,
                    staging_dirname,  # new working_dir
                    True)  # is re-entrant
            else:
                absolute_path = os.path.join(
                    staging_dirname,
                    relative_path,
                    )
                log('Signing %s...\n' % absolute_path)
                sign(absolute_path, dictionary['entitlements'])

    zip_stats(zip_path)
    log('Updating %s with signed files...\n' % zip_path)
    # update downloaded zip
    update_zip(staging_dirname, zip_path)
    zip_stats(zip_path)

    # We should only notarize and upload to GS at top level
    if not is_reentrant:
        log('Uploading %s to notary service...\n' % zip_path)
        notarize(zip_path)
        log('Uploading to %s' % input_cloud_path)
        upload(zip_path, input_cloud_path)

    success_message(zip_path)
    log('Removing dir %s...\n' % staging_dirname)
    shutil.rmtree(staging_dirname)

    log('Finished processing %s...\n' % input_cloud_path)
    # Only write logfile for top-level archives
    if not is_reentrant:
        dirname = os.path.join(get_logs_dir(), 'archive_runs')
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        logfile_path = os.path.join(
            dirname,
            '%f_%s.log' % (
                time.time(),
                unique_filename))
        write_log_to_file(logfile_path)


def main(args):
    '''Application entrypoint'''
    ensure_entitlements_file()

    print 'Clean build folders...\n'
    clean()

    if args[0] == '--verify':
        request_uuid = args[1]
        poll_and_check_status(request_uuid)
    else:
        commit = args[0]

        for archive in ARCHIVES:
            process_archive(archive, commit, os.path.join(CWD, 'staging'))


# validations
for key in [
        'APP_SPECIFIC_PASSWORD',
        'CODESIGN_USERNAME',
        'CODESIGN_CERT_NAME']:
    if os.environ.get(key, None) is None:
        print 'Please provide the env variable %s' % key
        exit(1)

APP_SPECIFIC_PASSWORD = os.environ['APP_SPECIFIC_PASSWORD']
CODESIGN_PRIMARY_BUNDLE_ID = os.environ.get(
    'CODESIGN_PRIMARY_BUNDLE_ID',
    'com.example.arbitrary')
CODESIGN_USERNAME = os.environ['CODESIGN_USERNAME']
CODESIGN_CERT_NAME = os.environ['CODESIGN_CERT_NAME']


if len(sys.argv) == 1:
    usage()
    exit(1)

main(sys.argv[1:])
