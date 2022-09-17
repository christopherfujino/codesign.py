#!/usr/bin/env python3
'''Hello world'''

import json
import os
import re
import shutil
import subprocess
import sys
import time

ARCHIVES = [
    {
        'path': 'android-arm-profile/darwin-x64.zip',
        'files_with_entitlements': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'android-arm-release/darwin-x64.zip',
        'files_with_entitlements': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'android-arm64-release/darwin-x64.zip',
        'files_with_entitlements': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'android-arm64-profile/darwin-x64.zip',
        'files_with_entitlements': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'android-x64-profile/darwin-x64.zip',
        'files_with_entitlements': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'android-x64-release/darwin-x64.zip',
        'files_with_entitlements': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'dart-sdk-darwin-arm64.zip',
        'files_with_entitlements': [
            'dart-sdk/bin/dart',
            'dart-sdk/bin/dartaotruntime',
            'dart-sdk/bin/utils/gen_snapshot',
            ],
        },
    {
        'path': 'dart-sdk-darwin-x64.zip',
        'files_with_entitlements': [
            'dart-sdk/bin/dart',
            'dart-sdk/bin/dartaotruntime',
            'dart-sdk/bin/utils/gen_snapshot',
            ],
        },
    {
        'path': 'darwin-x64/artifacts.zip',
        'files_with_entitlements': [
            'flutter_tester',
            'gen_snapshot',
            'impellerc',
            'libtessellator.dylib',
            ],
        },
    {
        'path': 'darwin-x64-profile/artifacts.zip',
        'files_with_entitlements': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'darwin-x64-release/artifacts.zip',
        'files_with_entitlements': [
            'gen_snapshot',
            ],
        },
    {
        'path': 'darwin-x64/gen_snapshot.zip',
        'files_with_entitlements': [
            'gen_snapshot_arm64',
            'gen_snapshot_x64',
            ],
        },
    {
        'path': 'darwin-x64-profile/gen_snapshot.zip',
        'files_with_entitlements': [
            'gen_snapshot_arm64',
            'gen_snapshot_x64',
            ],
        },
    {
        'path': 'darwin-x64-release/gen_snapshot.zip',
        'files_with_entitlements': [
            'gen_snapshot_arm64',
            'gen_snapshot_x64',
            ],
        },
    {
        'path': 'darwin-x64/font-subset.zip',
        'files': [
            'font-subset',
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
        'path': 'darwin-x64-profile/FlutterMacOS.framework.zip',
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
        'path': 'darwin-x64-release/FlutterMacOS.framework.zip',
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
        'path': 'ios/artifacts.zip',
        'files': [
            {
                'path': 'Flutter.framework.zip',
                'files': [
                    'Flutter',
                    ],
                },
            'Flutter.xcframework/ios-arm64_x86_64-simulator/Flutter.framework/Flutter',
            ],
        'files_with_entitlements': [
            'gen_snapshot_arm64',
            ],
        },
    {
        'path': 'ios-profile/artifacts.zip',
        'files_with_entitlements': [
            'gen_snapshot_arm64',
            ],
        'files': [
            {
                'path': 'Flutter.framework.zip',
                'files': [
                    'Flutter',
                    ]
                },
            'Flutter.xcframework/ios-arm64_x86_64-simulator/Flutter.framework/Flutter',
            ],
        },
    {
        'path': 'ios-release/artifacts.zip',
        'files_with_entitlements': [
            'gen_snapshot_arm64',
            ],
        'files': [
            {
                'path': 'Flutter.framework.zip',
                'files': [
                    'Flutter',
                    ]
                },
            'Flutter.xcframework/ios-arm64_x86_64-simulator/Flutter.framework/Flutter',
            ],
        },
]

CWD = os.getcwd()

LOG = []

STARTING_TIME = int(time.time())


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
        print(message)
    # This is used for logging out zip contents
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


def log_and_exit(message, exit_code=1, file_name='crasher.log'):
    '''Flush log then exit'''
    log(message)
    write_log_to_file(os.path.join(get_logs_dir(), file_name))
    exit(exit_code)


def shasum(path_to_file):
    '''log out the shasum of a file'''
    sha = run_and_return_output(['shasum', path_to_file])
    log(sha)
    return sha

def check_xcode_version():
    isNotaryTool = True
    log('checking Xcode version...')
    command = [
        'xcodebuild',
        '-version',
        ]
    outArray = run_and_return_output(command)
    log('out: %s' % '\n'.join(outArray))
    xcode_version = int(outArray[0].split()[1].split('.')[0])
    if xcode_version <= 12:
        isNotaryTool = False
    log('based on your xcode major version of '+ str(xcode_version)+
        ', the decision to use notarytool is '+str(isNotaryTool))
    return isNotaryTool

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

    print('''
    Usage:
    codesign.py <engine-commit-hash>
    ''')


def validate_command(command_name):
    '''Validate the given command exists on PATH'''

    if subprocess.call(['which', command_name]) != 0:
        print('You don\'t appear to have "%s" installed.' % command_name)
        exit(1)


def create_working_dir(parent):
    '''Clean our build folders'''
    dirname = os.path.join(parent, '%i_session' % STARTING_TIME)
    os.mkdir(dirname)
    get_logs_dir()
    return dirname


def ensure_entitlements_file():
    '''Write entitlements file if it does not exist'''
    entitlements_path = os.path.join(CWD, 'Entitlements.plist')
    if not os.path.isfile(entitlements_path):
        log_and_exit('Error! No Entitlements.plist file found!')


def get_unique_filename(url):
    '''Generates a filename based on input url'''
    return url.replace('/', '_')


def download(cloud_path, local_dest_path):
    '''Download supplied Google Storage URI'''
    if os.path.isfile(local_dest_path):
        log('Skipping download of %s, already exists locally\n' % cloud_path)
        return False

    log('Downloading %s...\n' % cloud_path)

    command = [
        'gsutil',
        'cp',
        cloud_path,
        local_dest_path,
        ]
    exit_code = subprocess.call(command)
    return exit_code == 0
    #if exit_code != 0:
    #    log_and_exit('Download of %s failed!' % cloud_path, exit_code)


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
        log('Unzipping of %s failed' % file_path)
        return None
    return archive_dirname


def get_binary_names(config):
    '''Returns names of binary files to sign/notarize from dict'''
    return config['binary_paths']


def validate_binary_exists(path):
    '''Validate a binary file listed in config exists'''
    return os.path.isfile(path)


def sign(path, with_entitlements=False):
    '''Sign a single binary'''
    log('Signing %s...' % path)
    command = [
        'codesign',
        '-f',  # force
        '-s',  # use the cert provided by next argument
        CODESIGN_CERT_NAME,
        path,
        '--timestamp',  # add a secure timestamp
        '--options=runtime',  # hardened runtime
        ]
    if with_entitlements:
        command += ['--entitlements', './Entitlements.plist']
    exit_code = subprocess.call(command)
    if exit_code != 0:
        log_and_exit('Error while attempting to sign %s' % path, exit_code)


def run_and_return_output(command):
    '''Takes in list/string of command, returns list of stdout'''
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True)
    return proc.stdout.readlines() + proc.stderr.readlines()


def get_logs_dir():
    '''Ensure exists, and return path to global logs dir'''
    log_dir = os.path.join(CWD, '%i_%s_logs' % (STARTING_TIME, sys.argv[1]))
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


def upload_zip_to_notary(archive_path, isNotaryTool):
    '''Uploads zip file to the notary service'''
    # Sometimes this flakes, so try twice
    attempts_left = 5
    while attempts_left > 0:
        log('Initiating upload of file %s to notary service...' % archive_path)
        if isNotaryTool:
            command = [
            'xcrun',
            'notarytool',
            'submit',
            archive_path,
            '--apple-id',
            CODESIGN_APPSTORE_ID,
            '--password',
            APP_SPECIFIC_PASSWORD,
            '--team-id',
            CODESIGN_TEAM_ID,
            ]
        else:
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
            ]

        # Note that this tool outputs to STDOUT on Xcode 11, STDERR on earlier
        out = '\n'.join(run_and_return_output(command))
        log('out: %s' % out)

        if isNotaryTool:
            match = re.search('id: ([a-z0-9-]+)', out)
        else:
            match = re.search('RequestUUID = ([a-z0-9-]+)', out)
        if not match:
            log('Unrecognized output from: %s' % ' '.join(command))
            attempts_left -= 1
            # wait 2 seconds before trying again
            time.sleep(4)
            continue

        request_uuid = match.group(1)
        log('Your RequestUUID is: %s' % request_uuid)

        return request_uuid

    log_and_exit(
            'Failed to upload file %s to the notary service' % archive_path)


def check_status(uuid, isNotaryTool):
    '''Check the status of our request'''
    if isNotaryTool:
        command = [
            'xcrun',
            'notarytool',
            'info',
            uuid,
            '--password',
            APP_SPECIFIC_PASSWORD,
            '--apple-id',
            CODESIGN_APPSTORE_ID,
            '--team-id',
            CODESIGN_TEAM_ID,
            ]
    else:
        command = [
            'xcrun',
            'altool',
            '--notarization-info',
            uuid,
            '-u',
            CODESIGN_USERNAME,
            '--password',
            APP_SPECIFIC_PASSWORD,
            ]

    log('Checking on the status of request: %s' % uuid)
    # Note that this tool outputs to STDOUT on Xcode 11, STDERR on earlier
    output = '\n'.join(run_and_return_output(command))
    log(output)

    if isNotaryTool:
        match = re.search('[ ]*status: ([a-zA-z ]+)', output)
    else:
        match = re.search('[ ]*Status: ([a-z ]+)', output)
    if not match:
        log_and_exit('Unrecognized output from: %s' % ' '.join(command))

    status = match.group(1)
    if isNotaryTool:
        if status == 'Accepted': 
            return True
        if status == 'In Progress': 
            log('Notarization is still pending...\n')
            return False

        return log_and_exit('Notarization failed with: %s' % status)
    else:
        if status == 'success':
            return True
        if status == 'in progress':
            log('Notarization is still pending...\n')
            return False

        return log_and_exit('Notarization failed with: %s' % status)


def notarize(archive_path, isNotaryTool):
    '''Notarize given archive zip'''
    return upload_zip_to_notary(archive_path, isNotaryTool)


def success_message(output_archive):
    '''Print success message.'''
    log('Your notarization of %s was successful.' % output_archive)


def process_zip(
        zip_path,
        config,
        ):
    '''Recursive'''
    shasum(zip_path)

    log('Unzipping archive at %s...\n' % zip_path)
    staging_dirname = unzip_archive(zip_path)
    if staging_dirname == None:
        log('Cancelling processing of %s' % zip_path)
        return

    log('Validating config...\n')
    files = [
        {'path': path, 'entitlements': False} for path in config.get('files', [])]
    files_with_entitlements = [
        {'path': path, 'entitlements': True} for path in config.get('files_with_entitlements', [])]
    all_files = files + files_with_entitlements
    for file_dict in all_files:
        if isinstance(file_dict['path'], dict):
            continue
        absolute_path = os.path.join(staging_dirname, file_dict['path'])
        if not validate_binary_exists(absolute_path):
            log_and_exit('Cannot find file %s from config' % absolute_path)

    log('Signing binaries...\n')
    for file_dict in all_files:
        if isinstance(file_dict['path'], dict):
            next_config = file_dict['path']
            next_zip_path = os.path.join(staging_dirname, next_config['path'])
            log('Recursing for %s' % next_zip_path)
            process_zip(next_zip_path, next_config)
        else:
            absolute_path = os.path.join(
                staging_dirname,
                file_dict['path'],
                )
            log('Signing %s...\n' % absolute_path)
            sign(absolute_path, file_dict['entitlements'])

    log('Updating %s with signed files...\n' % zip_path)
    # update downloaded zip
    update_zip(staging_dirname, zip_path)
    shasum(zip_path)

    log('Removing dir %s...\n' % staging_dirname)
    shutil.rmtree(staging_dirname)

    log('Finished processing %s...\n' % zip_path)


def process_archive(
        input_storage_base_url,
        output_storage_base_url,
        config,
        commit,
        working_dir,
        isNotaryTool):
    '''Main execution'''
    input_cloud_path = '%s/%s/%s' % (
        input_storage_base_url,
        commit,
        config['path'])

    unique_filename = get_unique_filename(config['path'])
    zip_path = os.path.join(
        working_dir,
        unique_filename)

    log('Beginning processing of %s...\n' % config['path'])

    if not download(input_cloud_path, zip_path):
        log('Download of %s failed, skipping.\n' % config['path'])
        return None

    output_cloud_path = '%s/%s/%s' % (
        output_storage_base_url,
        commit,
        config['path'])

    process_zip(zip_path, config)

    # Only notarize & write logfile for top-level archives
    log('Uploading %s to notary service...\n' % zip_path)
    request_uuid = notarize(zip_path, isNotaryTool)

    # Return this dict for later verifying of the notarization & uploading
    return {
        'output_cloud_path': output_cloud_path,
        'uuid': request_uuid,
        'zip_path': zip_path,
        }


def verify_and_upload(request, isNotaryTool):
    '''Given a notarization request, check for its status & upload if done'''
    # Only upload if notarization was successful
    result = check_status(request['uuid'], isNotaryTool)
    if result:
        log('Uploading to %s' % request['output_cloud_path'])
        upload(request['zip_path'], request['output_cloud_path'])

    return result


def main(args, bucket_prefix):
    '''Application entrypoint'''
    ensure_entitlements_file()

    print('Clean build folders...\n')
    working_dir = create_working_dir(CWD)

    requests = []
    skipped_archives = []

    isNotaryTool = check_xcode_version()
    optional_switch = re.search('^--([a-z-]+)', args[0])
    if args[0] == '--verify':
        request_uuid = args[1]
        check_status(request_uuid, isNotaryTool)
    elif optional_switch:
        name = optional_switch.group(1)
        libimobiledevice_archives = {
            'ios-deploy': {
                'path': 'ios-deploy.zip',
                'files': ['ios-deploy'],
                },
            'libimobiledevice': {
                'path': 'libimobiledevice.zip',
                'files_with_entitlements': [
                    'idevicescreenshot',
                    'idevicesyslog',
                    'libimobiledevice-1.0.6.dylib',
                    ],
                },
            'libplist': {
                'path': 'libplist.zip',
                'files_with_entitlements': [
                    'libplist-2.0.3.dylib',
                    ],
                },
            'usbmuxd': {
                'path': 'usbmuxd.zip',
                'files_with_entitlements': [
                    'iproxy',
                    'libusbmuxd-2.0.6.dylib',
                    ],
                },
            'openssl': {
                'path': 'openssl.zip',
                'files_with_entitlements': [
                    'libssl.1.1.dylib',
                    'libcrypto.1.1.dylib',
                    ],
                },
            }
        archive = libimobiledevice_archives[name]
        if not archive:
            log('Unknown option %s' % args[0])
            exit(1)
        request = process_archive(
            'gs://%s/ios-usb-dependencies/unsigned/%s' % (bucket_prefix, name),
            'gs://%s/ios-usb-dependencies/%s' % (bucket_prefix, name),
            libimobiledevice_archives[name],
            args[1],
            working_dir,
            isNotaryTool
        )
        if request == None:
            skipped_archives.append(name)
        else:
            requests.append(request)
    else:
        engine_revision = args[0]
        requests = []
        log('Beginning codesigning of engine revision %s' % engine_revision)
        for archive in ARCHIVES:
            requests.append(process_archive(
                'gs://%s/flutter' % bucket_prefix,
                'gs://%s/flutter' % bucket_prefix,
                archive,
                engine_revision,
                working_dir,
                isNotaryTool))

    index = 0
    last_at_zero = time.time()

    # Sleep here so that we never check for a job before it has been started,
    # leading to an error from the notary service.
    time.sleep(45)

    # Minimum time between successive requests for the same archive
    timeout_seconds = 20

    # Iterate until requests is empty
    while requests:
        now = time.time()
        log('%i requests left' % len(requests))
        time_since_last_at_zero = now - last_at_zero
        # Ensure we never hit server more than twice in 10 seconds
        # for a particular request
        if time_since_last_at_zero < timeout_seconds:
            timeout = timeout_seconds - time_since_last_at_zero
            log('Waiting %i seconds until next check...' % timeout)
            time.sleep(timeout)

        request = requests[index]
        if verify_and_upload(request, isNotaryTool):
            # remove from list...same index now points to next request...
            requests.remove(request)
        else:
            # Leave in list but move on to next request
            index += 1
        if index >= len(requests):
            index = 0
            last_at_zero = time.time()

    # Clean up signed binaries
    shutil.rmtree(working_dir)

    if len(skipped_archives) > 0:
        log('Skipped the following archives which were not found on '
                'cloud storage:\n%s' % '\n'.join(skipped_archives))

    log('Codesigning & Notarization successful')


# validations
for key in [
        'APP_SPECIFIC_PASSWORD',
        'CODESIGN_USERNAME',
        'CODESIGN_CERT_NAME',
        'CODESIGN_APPSTORE_ID',
        'CODESIGN_APPSTORE_PASSWORD',
        'CODESIGN_TEAM_ID',
        ]:
    if os.environ.get(key, None) is None:
        print('Please provide the env variable %s' % key)
        exit(1)

APP_SPECIFIC_PASSWORD = os.environ['APP_SPECIFIC_PASSWORD']
CODESIGN_PRIMARY_BUNDLE_ID = os.environ.get(
    'CODESIGN_PRIMARY_BUNDLE_ID',
    'dev.flutter.tools')
CODESIGN_USERNAME = os.environ['CODESIGN_USERNAME']
CODESIGN_CERT_NAME = os.environ['CODESIGN_CERT_NAME']

CODESIGN_APPSTORE_ID = os.environ['CODESIGN_APPSTORE_ID']
CODESIGN_TEAM_ID = os.environ['CODESIGN_TEAM_ID']


if len(sys.argv) == 1:
    usage()
    exit(1)

main(sys.argv[1:], 'flutter_infra_release')

log_and_exit('Success', 0, 'notarization.log')
