# Codesigning Script

This script will--given a particular Flutter Engine revision--fetch the
necessary cache artifacts and codesign & notarize them. Pre-requisites are:

1. You must have `gsutil` installed and authenticated to write to the
flutter-infra bucket.
1. The following env variables must be set: `CODESIGN_USERNAME`,
`CODESIGN_CERT_NAME`, `APP_SPECIFIC_PASSWORD`. There is an internal doc that
has more information on these.
1. Xcode must be installed, and a Developer ID certificate must be present
in the keychain (the name of this cert should be `CODESIGN_CERT_NAME`)

Usage is as follows:

`./codesign.py <engine_revision_hash>`
